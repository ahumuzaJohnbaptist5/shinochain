'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import { getFeed, type Video } from '@/lib/api';
import FeedItem from '@/components/FeedItem';

export default function FeedPage() {
  const router = useRouter();
  const [videos, setVideos] = useState<Video[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);
  // Holds refs to each feed item element for IntersectionObserver
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Auth guard
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
    }
  }, [router]);

  // Initial feed load
  const loadFeed = useCallback(async (nextCursor?: string) => {
    try {
      const data = await getFeed(nextCursor);
      if (nextCursor) {
        setVideos((prev) => [...prev, ...data.videos]);
      } else {
        setVideos(data.videos);
      }
      setCursor(data.next_cursor);
      setHasMore(data.next_cursor !== null);
    } catch {
      setError('Failed to load feed. Please try again.');
    }
  }, []);

  useEffect(() => {
    loadFeed().finally(() => setLoading(false));
  }, [loadFeed]);

  // IntersectionObserver — detect which item is centred in the viewport
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    itemRefs.current.forEach((el, index) => {
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setActiveIndex(index);
          }
        },
        { threshold: 0.6 },
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach((o) => o.disconnect());
  }, [videos]);

  // Sentinel IntersectionObserver — load more when near bottom
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const obs = new IntersectionObserver(
      async ([entry]) => {
        if (entry.isIntersecting && hasMore && !loadingMore) {
          setLoadingMore(true);
          await loadFeed(cursor ?? undefined);
          setLoadingMore(false);
        }
      },
      { threshold: 0.1 },
    );
    obs.observe(sentinel);
    return () => obs.disconnect();
  }, [hasMore, loadingMore, cursor, loadFeed]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="w-8 h-8 border-2 border-brand-pink border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-black gap-4 px-4">
        <p className="text-red-400 text-center">{error}</p>
        <button
          onClick={() => { setError(null); setLoading(true); loadFeed().finally(() => setLoading(false)); }}
          className="px-4 py-2 bg-brand-pink rounded-lg text-sm font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-black gap-3 px-4">
        <p className="text-3xl">🎬</p>
        <p className="text-zinc-400 text-center">No videos yet. Be the first to upload!</p>
        <button
          onClick={() => router.push('/upload')}
          className="px-4 py-2 bg-brand-cyan text-black rounded-lg text-sm font-semibold"
        >
          Upload video
        </button>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-screen overflow-y-scroll snap-y snap-mandatory"
    >
      {videos.map((video, index) => (
        <div
          key={video.id}
          ref={(el) => { itemRefs.current[index] = el; }}
          className="snap-start"
        >
          <FeedItem video={video} isActive={index === activeIndex} />
        </div>
      ))}

      {/* Sentinel for infinite scroll */}
      <div ref={sentinelRef} className="h-1" />

      {loadingMore && (
        <div className="h-16 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Upload FAB */}
      <button
        onClick={() => router.push('/upload')}
        className="fixed top-4 right-4 z-50 w-10 h-10 bg-brand-pink rounded-full flex items-center justify-center text-white text-xl shadow-lg hover:bg-pink-600 transition-colors"
        aria-label="Upload video"
      >
        +
      </button>
    </div>
  );
}
