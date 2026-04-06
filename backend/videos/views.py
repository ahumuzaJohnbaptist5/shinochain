import uuid
import logging
import boto3
from botocore.config import Config
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import meilisearch

from .models import Video
from .serializers import PublishVideoSerializer, VideoSerializer
from worker.tasks import process_video

logger = logging.getLogger(__name__)


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


_ALLOWED_CONTENT_TYPES = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/x-msvideo": "avi",
    "video/webm": "webm",
}


class PresignedUploadView(APIView):
    """Return a presigned PUT URL for direct browser-to-R2 upload."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        content_type = request.data.get("content_type", "video/mp4")
        ext = _ALLOWED_CONTENT_TYPES.get(content_type)
        if ext is None:
            return Response(
                {"detail": f"Unsupported content_type. Allowed: {', '.join(_ALLOWED_CONTENT_TYPES)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        key = f"uploads/{request.user.id}/{uuid.uuid4()}.{ext}"
        try:
            client = _s3_client()
            url = client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=3600,
            )
        except Exception:
            logger.exception("Failed to generate presigned URL for user %s", request.user.id)
            return Response({"detail": "Could not generate upload URL."}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"upload_url": url, "key": key})


class PublishVideoView(APIView):
    """Create a Video record and enqueue background processing."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PublishVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        video = Video.objects.create(
            user=request.user,
            upload_key=data["upload_key"],
            caption=data["caption"],
            hashtags=data["hashtags"],
            duration=data.get("duration"),
            status=Video.STATUS_PENDING,
        )
        process_video.delay(str(video.id))
        return Response(VideoSerializer(video).data, status=status.HTTP_201_CREATED)


class FeedView(generics.ListAPIView):
    """Cursor-based feed of ready videos ordered by newest first."""

    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Video.objects.filter(status=Video.STATUS_READY).select_related("user")
        cursor = self.request.query_params.get("cursor")
        if cursor:
            qs = qs.filter(created_at__lt=cursor)
        return qs.order_by("-created_at")[: 20]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        items = serializer.data
        next_cursor = None
        if len(items) == 20:
            last = qs.last()
            next_cursor = last.created_at.isoformat() if last else None
        return Response({"videos": items, "next_cursor": next_cursor})


class SearchView(APIView):
    """Full-text search via Meilisearch."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        q = request.query_params.get("q", "")
        try:
            client = meilisearch.Client(
                settings.MEILISEARCH_URL, settings.MEILISEARCH_MASTER_KEY
            )
            results = client.index("videos").search(q, {"limit": 20})
        except Exception:
            logger.exception("Meilisearch search error")
            return Response({"detail": "Search service unavailable."}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(results)
