'use client';

import { useEffect, useRef } from 'react';
import Hls from 'hls.js';

interface VideoPlayerProps {
  src: string;
  poster?: string;
  videoId: string;
  videoRef?: React.RefObject<HTMLVideoElement>;
}

export default function VideoPlayer({
  src,
  poster,
  videoId,
  videoRef: externalRef,
}: VideoPlayerProps) {
  const internalRef = useRef<HTMLVideoElement>(null);
  const videoRef = externalRef ?? internalRef;
  const hlsRef = useRef<Hls | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    // Destroy any previous HLS instance
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
      });
      hlsRef.current = hls;
      hls.loadSource(src);
      hls.attachMedia(video);
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError();
              break;
            default:
              hls.destroy();
          }
        }
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = src;
    }

    return () => {
      hlsRef.current?.destroy();
      hlsRef.current = null;
    };
  }, [src, videoRef]);

  return (
    <video
      ref={videoRef}
      poster={poster}
      data-video-id={videoId}
      loop
      playsInline
      muted
      preload="metadata"
      className="w-full h-full object-cover"
    />
  );
}
