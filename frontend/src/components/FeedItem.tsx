'use client';

import { useRef, useState, useCallback } from 'react';
import VideoPlayer from './VideoPlayer';
import {
  likeVideo,
  unlikeVideo,
  getComments,
  postComment,
  followUser,
  type Video,
  type Comment,
} from '@/lib/api';

interface FeedItemProps {
  video: Video;
  isActive: boolean;
}

export default function FeedItem({ video, isActive }: FeedItemProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // Like state — optimistic update
  const [liked, setLiked] = useState(video.is_liked);
  const [likesCount, setLikesCount] = useState(video.likes_count);
  const [likeLoading, setLikeLoading] = useState(false);

  // Comment panel
  const [commentsOpen, setCommentsOpen] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [commentPosting, setCommentPosting] = useState(false);

  // Follow state
  const [following, setFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  // Sync play/pause with parent's IntersectionObserver
  const prevActive = useRef(false);
  if (isActive !== prevActive.current) {
    prevActive.current = isActive;
    const vid = videoRef.current;
    if (vid) {
      if (isActive) {
        vid.play().catch(() => {});
      } else {
        vid.pause();
      }
    }
  }

  const handleLike = useCallback(async () => {
    if (likeLoading) return;
    setLikeLoading(true);
    const wasLiked = liked;
    // Optimistic
    setLiked(!wasLiked);
    setLikesCount((c) => c + (wasLiked ? -1 : 1));
    try {
      if (wasLiked) {
        await unlikeVideo(video.id);
      } else {
        await likeVideo(video.id);
      }
    } catch {
      // Roll back on failure
      setLiked(wasLiked);
      setLikesCount((c) => c + (wasLiked ? 1 : -1));
    } finally {
      setLikeLoading(false);
    }
  }, [liked, likeLoading, video.id]);

  const handleOpenComments = useCallback(async () => {
    setCommentsOpen((o) => !o);
    if (!commentsOpen && comments.length === 0) {
      setCommentsLoading(true);
      try {
        const fetched = await getComments(video.id);
        setComments(fetched);
      } catch {
        // silently ignore
      } finally {
        setCommentsLoading(false);
      }
    }
  }, [commentsOpen, comments.length, video.id]);

  const handlePostComment = useCallback(async () => {
    if (!commentText.trim() || commentPosting) return;
    setCommentPosting(true);
    try {
      const newComment = await postComment(video.id, commentText.trim());
      setComments((prev) => [newComment, ...prev]);
      setCommentText('');
    } catch {
      // silently ignore
    } finally {
      setCommentPosting(false);
    }
  }, [commentText, commentPosting, video.id]);

  const handleFollow = useCallback(async () => {
    if (followLoading) return;
    setFollowLoading(true);
    const wasFollowing = following;
    setFollowing(!wasFollowing);
    try {
      if (wasFollowing) {
        await followUser(video.user.id); // unfollowUser would be symmetric
      } else {
        await followUser(video.user.id);
      }
    } catch {
      setFollowing(wasFollowing);
    } finally {
      setFollowLoading(false);
    }
  }, [following, followLoading, video.user.id]);

  return (
    <div className="relative w-full h-screen flex-shrink-0 overflow-hidden bg-black snap-start">
      {/* Video */}
      <div className="absolute inset-0">
        <VideoPlayer
          src={video.hls_manifest_url}
          poster={video.thumbnail_url}
          videoId={video.id}
          videoRef={videoRef}
        />
      </div>

      {/* Gradient overlays */}
      <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-black/80 to-transparent pointer-events-none" />
      <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-black/40 to-transparent pointer-events-none" />

      {/* Right sidebar actions */}
      <div className="absolute right-3 bottom-32 flex flex-col items-center gap-6">
        {/* Avatar + follow */}
        <div className="flex flex-col items-center gap-1">
          <div className="w-11 h-11 rounded-full bg-zinc-700 overflow-hidden border-2 border-white">
            {video.user.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={video.user.avatar_url}
                alt={video.user.username}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-lg font-bold">
                {video.user.username[0]?.toUpperCase()}
              </div>
            )}
          </div>
          <button
            onClick={handleFollow}
            disabled={followLoading}
            className="w-5 h-5 rounded-full bg-brand-pink flex items-center justify-center text-white text-xs font-bold disabled:opacity-50"
          >
            {following ? '✓' : '+'}
          </button>
        </div>

        {/* Like */}
        <button
          onClick={handleLike}
          disabled={likeLoading}
          className="flex flex-col items-center gap-1 disabled:opacity-50"
          aria-label={liked ? 'Unlike' : 'Like'}
        >
          <span className={`text-3xl transition-transform active:scale-125 ${liked ? 'text-brand-pink' : 'text-white'}`}>
            {liked ? '❤️' : '🤍'}
          </span>
          <span className="text-xs font-semibold">{likesCount.toLocaleString()}</span>
        </button>

        {/* Comments */}
        <button
          onClick={handleOpenComments}
          className="flex flex-col items-center gap-1"
          aria-label="Comments"
        >
          <span className="text-3xl">💬</span>
          <span className="text-xs font-semibold">{video.comments_count.toLocaleString()}</span>
        </button>
      </div>

      {/* Bottom info */}
      <div className="absolute left-3 bottom-6 right-20 pr-2">
        <p className="font-semibold text-sm mb-1">@{video.user.username}</p>
        <p className="text-sm text-zinc-200 line-clamp-2">{video.caption}</p>
        {video.hashtags.length > 0 && (
          <p className="text-xs text-brand-cyan mt-1 line-clamp-1">
            {video.hashtags.map((tag) => `#${tag}`).join(' ')}
          </p>
        )}
      </div>

      {/* Comments panel */}
      {commentsOpen && (
        <div className="absolute inset-x-0 bottom-0 h-2/3 bg-zinc-900/95 rounded-t-2xl flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-700">
            <h3 className="font-semibold text-sm">Comments</h3>
            <button
              onClick={() => setCommentsOpen(false)}
              className="text-zinc-400 hover:text-white text-lg leading-none"
              aria-label="Close comments"
            >
              ×
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-2 space-y-3">
            {commentsLoading ? (
              <p className="text-zinc-400 text-sm text-center py-4">Loading…</p>
            ) : comments.length === 0 ? (
              <p className="text-zinc-400 text-sm text-center py-4">No comments yet.</p>
            ) : (
              comments.map((c) => (
                <div key={c.id} className="flex gap-2">
                  <span className="font-semibold text-xs text-zinc-300 shrink-0">
                    @{c.user.username}
                  </span>
                  <span className="text-xs text-zinc-200">{c.text}</span>
                </div>
              ))
            )}
          </div>

          <div className="flex gap-2 px-4 py-3 border-t border-zinc-700">
            <input
              type="text"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePostComment()}
              placeholder="Add a comment…"
              className="flex-1 bg-zinc-800 rounded-full px-4 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-brand-cyan"
            />
            <button
              onClick={handlePostComment}
              disabled={commentPosting || !commentText.trim()}
              className="text-brand-cyan font-semibold text-sm disabled:opacity-40"
            >
              Post
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
