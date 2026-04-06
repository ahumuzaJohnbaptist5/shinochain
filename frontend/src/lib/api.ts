import axios from 'axios';

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000') + '/api';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Token helpers
// NOTE: localStorage is used here for simplicity. In production, prefer
// HttpOnly cookies (set by the server) to protect against XSS attacks.
// ---------------------------------------------------------------------------
const TOKEN_KEY = 'shinochain_jwt';

export function saveToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// Attach JWT to every outgoing request
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface AuthResponse {
  access: string;
  refresh: string;
}

export async function register(
  email: string,
  username: string,
  password: string,
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', { email, username, password });
  return data;
}

export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', {
    email,
    password,
  });
  return data;
}

// ---------------------------------------------------------------------------
// User
// ---------------------------------------------------------------------------
export interface User {
  id: string;
  username: string;
  email: string;
  avatar_url?: string;
  bio?: string;
  followers_count: number;
  following_count: number;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>('/me');
  return data;
}

export async function followUser(userId: string): Promise<void> {
  await api.post(`/users/${userId}/follow`);
}

export async function unfollowUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}/follow`);
}

// ---------------------------------------------------------------------------
// Videos
// ---------------------------------------------------------------------------
export interface PresignedUrlResponse {
  upload_url: string;
  key: string;
}

export async function getPresignedUrl(
  filename: string,
  contentType: string,
): Promise<PresignedUrlResponse> {
  const { data } = await api.post<PresignedUrlResponse>('/uploads/video', {
    filename,
    content_type: contentType,
  });
  return data;
}

export interface PublishVideoPayload {
  upload_key: string;
  caption: string;
  hashtags: string[];
  duration?: number;
}

export interface Video {
  id: string;
  caption: string;
  hashtags: string[];
  hls_manifest_url: string;
  thumbnail_url: string;
  likes_count: number;
  comments_count: number;
  views_count: number;
  // VideoSerializer exposes username/avatar_url flat (not nested user object)
  username: string;
  avatar_url?: string;
  status: string;
  created_at: string;
}

export async function publishVideo(payload: PublishVideoPayload): Promise<Video> {
  const { data } = await api.post<Video>('/videos', payload);
  return data;
}

export interface FeedResponse {
  videos: Video[];
  next_cursor: string | null;
}

export async function getFeed(cursor?: string): Promise<FeedResponse> {
  const params = cursor ? { cursor } : {};
  const { data } = await api.get<FeedResponse>('/feed', { params });
  return data;
}

export async function likeVideo(videoId: string): Promise<void> {
  await api.post(`/videos/${videoId}/like`);
}

export async function unlikeVideo(videoId: string): Promise<void> {
  await api.delete(`/videos/${videoId}/like`);
}

// ---------------------------------------------------------------------------
// Comments
// ---------------------------------------------------------------------------
export interface Comment {
  id: string;
  text: string;
  user: Pick<User, 'id' | 'username' | 'avatar_url'>;
  created_at: string;
}

export async function getComments(videoId: string): Promise<Comment[]> {
  const { data } = await api.get<Comment[]>(`/videos/${videoId}/comments`);
  return data;
}

export async function postComment(
  videoId: string,
  text: string,
): Promise<Comment> {
  const { data } = await api.post<Comment>(`/videos/${videoId}/comments`, {
    text,
  });
  return data;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------
export interface SearchResults {
  videos: Video[];
  users: User[];
}

export async function search(q: string): Promise<SearchResults> {
  const { data } = await api.get<SearchResults>('/search', { params: { q } });
  return data;
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------
export interface AnalyticsEvent {
  event_type: string;
  video_id?: string;
  payload?: Record<string, unknown>;
  timestamp: string;
}

export async function postAnalyticsEvents(
  events: AnalyticsEvent[],
): Promise<void> {
  await api.post('/analytics/events', { events });
}
