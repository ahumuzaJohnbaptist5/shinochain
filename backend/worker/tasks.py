"""
Background Celery tasks for video processing pipeline:
  process_video  → chains transcode_video | generate_thumbnail | index_video
  transcode_video → ffmpeg HLS (360p, 720p, 1080p) → upload segments to R2
  generate_thumbnail → ffmpeg screenshot at 1 s → upload to R2
  index_video    → upsert document into Meilisearch 'videos' index
"""
import logging
import os
import subprocess
import tempfile
import uuid

import boto3
import meilisearch
from botocore.config import Config
from celery import chain, shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


def _upload_file(local_path: str, s3_key: str, content_type: str = "application/octet-stream") -> str:
    """Upload a local file to R2 and return its public key."""
    client = _s3_client()
    client.upload_file(
        local_path,
        settings.AWS_STORAGE_BUCKET_NAME,
        s3_key,
        ExtraArgs={"ContentType": content_type},
    )
    return s3_key


def _upload_directory(local_dir: str, s3_prefix: str) -> None:
    """Recursively upload all files in a local directory to R2."""
    client = _s3_client()
    for root, _dirs, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_key = f"{s3_prefix}/{relative_path}".replace("\\", "/")
            ext = filename.rsplit(".", 1)[-1].lower()
            content_type_map = {
                "m3u8": "application/vnd.apple.mpegurl",
                "ts": "video/mp2t",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
            }
            content_type = content_type_map.get(ext, "application/octet-stream")
            client.upload_file(
                local_path,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )


def _public_url(s3_key: str) -> str:
    """Build a public URL for an R2 object."""
    endpoint = settings.AWS_S3_ENDPOINT_URL.rstrip("/")
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    return f"{endpoint}/{bucket}/{s3_key}"


def _run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nstderr: {result.stderr}")
    return result


# ---------------------------------------------------------------------------
# HLS variant config
# ---------------------------------------------------------------------------

HLS_VARIANTS = [
    {"name": "360p",  "height": 360,  "bitrate": "800k",  "maxrate": "856k",  "bufsize": "1200k",  "audio": "96k"},
    {"name": "720p",  "height": 720,  "bitrate": "2800k", "maxrate": "2996k", "bufsize": "4200k",  "audio": "128k"},
    {"name": "1080p", "height": 1080, "bitrate": "5000k", "maxrate": "5350k", "bufsize": "7500k",  "audio": "192k"},
]


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def transcode_video(self, video_id: str):
    """
    Download the raw upload from R2, run ffmpeg to produce HLS variants,
    upload the segments back to R2, and update the Video record.
    """
    from videos.models import Video  # lazy import to avoid circular deps

    try:
        video = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        logger.error("transcode_video: Video %s not found", video_id)
        return

    video.status = Video.STATUS_PROCESSING
    video.save(update_fields=["status"])

    with tempfile.TemporaryDirectory(prefix="shinochain_transcode_") as tmpdir:
        # 1. Download source file from R2
        source_path = os.path.join(tmpdir, "source")
        try:
            client = _s3_client()
            client.download_file(
                settings.AWS_STORAGE_BUCKET_NAME,
                video.upload_key,
                source_path,
            )
        except Exception as exc:
            logger.exception("transcode_video: download failed for %s", video_id)
            video.status = Video.STATUS_FAILED
            video.save(update_fields=["status"])
            raise self.retry(exc=exc)

        hls_dir = os.path.join(tmpdir, "hls")
        os.makedirs(hls_dir, exist_ok=True)

        variant_playlists = []

        # 2. Encode each variant
        for variant in HLS_VARIANTS:
            v_name = variant["name"]
            v_dir = os.path.join(hls_dir, v_name)
            os.makedirs(v_dir, exist_ok=True)
            segment_pattern = os.path.join(v_dir, "seg%03d.ts")
            playlist_path = os.path.join(v_dir, "index.m3u8")

            cmd = [
                "ffmpeg", "-y", "-i", source_path,
                "-vf", f"scale=-2:{variant['height']}",
                "-c:v", "libx264", "-profile:v", "main",
                "-b:v", variant["bitrate"],
                "-maxrate", variant["maxrate"],
                "-bufsize", variant["bufsize"],
                "-c:a", "aac", "-b:a", variant["audio"],
                "-hls_time", "6",
                "-hls_playlist_type", "vod",
                "-hls_segment_filename", segment_pattern,
                playlist_path,
            ]
            try:
                _run(cmd)
            except RuntimeError as exc:
                logger.exception("transcode_video: ffmpeg failed for variant %s of %s", v_name, video_id)
                video.status = Video.STATUS_FAILED
                video.save(update_fields=["status"])
                raise self.retry(exc=exc)

            variant_playlists.append((v_name, variant["height"], variant["bitrate"]))

        # 3. Build master playlist
        master_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
        bandwidth_map = {v["name"]: v["bitrate"].replace("k", "000") for v in HLS_VARIANTS}
        for v_name, height, _bitrate in variant_playlists:
            bandwidth = bandwidth_map.get(v_name, "800000")
            master_lines.append(
                f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION=?x{height}'
            )
            master_lines.append(f"{v_name}/index.m3u8")
        master_path = os.path.join(hls_dir, "master.m3u8")
        with open(master_path, "w") as f:
            f.write("\n".join(master_lines) + "\n")

        # 4. Upload entire HLS directory to R2
        hls_prefix = f"hls/{video_id}"
        try:
            _upload_directory(hls_dir, hls_prefix)
        except Exception as exc:
            logger.exception("transcode_video: upload failed for %s", video_id)
            video.status = Video.STATUS_FAILED
            video.save(update_fields=["status"])
            raise self.retry(exc=exc)

    manifest_url = _public_url(f"{hls_prefix}/master.m3u8")
    video.hls_manifest_url = manifest_url
    video.save(update_fields=["hls_manifest_url"])
    logger.info("transcode_video: completed for %s → %s", video_id, manifest_url)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_thumbnail(self, video_id: str):
    """
    Download the raw upload from R2, take a screenshot at 1 s with ffmpeg,
    upload to R2, and update thumbnail_url on the Video record.
    """
    from videos.models import Video

    try:
        video = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        logger.error("generate_thumbnail: Video %s not found", video_id)
        return

    with tempfile.TemporaryDirectory(prefix="shinochain_thumb_") as tmpdir:
        source_path = os.path.join(tmpdir, "source")
        thumb_path = os.path.join(tmpdir, "thumbnail.jpg")

        try:
            client = _s3_client()
            client.download_file(
                settings.AWS_STORAGE_BUCKET_NAME,
                video.upload_key,
                source_path,
            )
        except Exception as exc:
            logger.exception("generate_thumbnail: download failed for %s", video_id)
            raise self.retry(exc=exc)

        cmd = [
            "ffmpeg", "-y", "-ss", "1",
            "-i", source_path,
            "-vframes", "1",
            "-q:v", "2",
            thumb_path,
        ]
        try:
            _run(cmd)
        except RuntimeError as exc:
            logger.exception("generate_thumbnail: ffmpeg failed for %s", video_id)
            raise self.retry(exc=exc)

        thumb_key = f"thumbnails/{video_id}.jpg"
        try:
            _upload_file(thumb_path, thumb_key, content_type="image/jpeg")
        except Exception as exc:
            logger.exception("generate_thumbnail: upload failed for %s", video_id)
            raise self.retry(exc=exc)

    video.thumbnail_url = _public_url(thumb_key)
    video.save(update_fields=["thumbnail_url"])
    logger.info("generate_thumbnail: completed for %s", video_id)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def index_video(self, video_id: str):
    """Upsert a video document into the Meilisearch 'videos' index."""
    from videos.models import Video

    try:
        video = Video.objects.select_related("user").get(pk=video_id)
    except Video.DoesNotExist:
        logger.error("index_video: Video %s not found", video_id)
        return

    document = {
        "id": str(video.id),
        "caption": video.caption,
        "hashtags": video.hashtags,
        "username": video.user.username,
        "thumbnail_url": video.thumbnail_url,
        "hls_manifest_url": video.hls_manifest_url,
        "likes_count": video.likes_count,
        "views_count": video.views_count,
        "created_at": video.created_at.isoformat(),
    }

    try:
        client = meilisearch.Client(
            settings.MEILISEARCH_URL, settings.MEILISEARCH_MASTER_KEY
        )
        index = client.index("videos")
        index.add_documents([document])
    except Exception as exc:
        logger.exception("index_video: Meilisearch error for %s", video_id)
        raise self.retry(exc=exc)

    # Mark video ready only after the full pipeline (transcode + thumbnail + index) completes
    Video.objects.filter(pk=video_id).update(status=Video.STATUS_READY)
    logger.info("index_video: indexed and marked ready %s", video_id)


@shared_task
def process_video(video_id: str):
    """
    Entry point: chains transcode → thumbnail → index.
    index_video sets status=ready on success at the end of the pipeline.
    """
    chain(
        transcode_video.si(video_id),
        generate_thumbnail.si(video_id),
        index_video.si(video_id),
    ).apply_async()
    logger.info("process_video: enqueued pipeline for %s", video_id)
