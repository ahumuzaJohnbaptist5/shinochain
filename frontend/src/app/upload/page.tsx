'use client';

import { useState, useRef, ChangeEvent, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { getPresignedUrl, publishVideo } from '@/lib/api';

type Step = 'pick' | 'upload' | 'details' | 'publishing';

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState<Step>('pick');
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [objectKey, setObjectKey] = useState('');

  const [caption, setCaption] = useState('');
  const [hashtagsRaw, setHashtagsRaw] = useState('');
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    handleUpload(selected);
  }

  async function handleUpload(selected: File) {
    setError(null);
    setStep('upload');
    setUploadProgress(0);
    try {
      const { upload_url, key } = await getPresignedUrl(
        selected.name,
        selected.type,
      );
      // PUT the file directly to R2 / S3 using the presigned URL
      await axios.put(upload_url, selected, {
        headers: { 'Content-Type': selected.type },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(pct);
          }
        },
      });
      setObjectKey(key);
      setStep('details');
    } catch {
      setError('Upload failed. Please try again.');
      setStep('pick');
    }
  }

  async function handlePublish(e: FormEvent) {
    e.preventDefault();
    if (!objectKey) return;
    setError(null);
    setStep('publishing');
    try {
      const hashtags = hashtagsRaw
        .split(/[\s,#]+/)
        .map((t) => t.trim().toLowerCase())
        .filter(Boolean);
      await publishVideo({ upload_key: objectKey, caption, hashtags });
      router.push('/');
    } catch {
      setError('Failed to publish. Please try again.');
      setStep('details');
    }
  }

  return (
    <main className="min-h-screen bg-black flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <button
          onClick={() => router.back()}
          className="text-zinc-400 hover:text-white text-sm mb-6 flex items-center gap-1"
        >
          ← Back
        </button>

        <h1 className="text-2xl font-bold mb-6">Upload video</h1>

        {/* Step: Pick file */}
        {(step === 'pick') && (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-zinc-600 hover:border-brand-cyan rounded-2xl p-12 flex flex-col items-center gap-3 cursor-pointer transition-colors"
          >
            <span className="text-5xl">🎥</span>
            <p className="text-zinc-300 text-sm font-medium text-center">
              Tap to select a video
            </p>
            <p className="text-zinc-500 text-xs text-center">MP4, MOV, WebM — up to 500 MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        )}

        {/* Step: Upload progress */}
        {step === 'upload' && (
          <div className="flex flex-col items-center gap-4 py-8">
            <p className="text-zinc-300 text-sm font-medium">
              Uploading {file?.name}…
            </p>
            <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-brand-cyan rounded-full transition-all duration-200"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-zinc-400 text-xs">{uploadProgress}%</p>
          </div>
        )}

        {/* Step: Details form */}
        {step === 'details' && (
          <form onSubmit={handlePublish} className="space-y-5">
            {previewUrl && (
              <video
                src={previewUrl}
                muted
                playsInline
                className="w-full rounded-xl aspect-[9/16] object-cover bg-zinc-900"
              />
            )}

            <div>
              <label htmlFor="caption" className="block text-sm font-medium text-zinc-300 mb-1">
                Caption
              </label>
              <textarea
                id="caption"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                rows={3}
                maxLength={300}
                placeholder="Describe your video…"
                className="w-full rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-brand-cyan resize-none"
              />
              <p className="text-right text-xs text-zinc-500 mt-0.5">
                {caption.length}/300
              </p>
            </div>

            <div>
              <label htmlFor="hashtags" className="block text-sm font-medium text-zinc-300 mb-1">
                Hashtags
              </label>
              <input
                id="hashtags"
                type="text"
                value={hashtagsRaw}
                onChange={(e) => setHashtagsRaw(e.target.value)}
                placeholder="#blockchain #crypto #shinochain"
                className="w-full rounded-lg bg-zinc-800 border border-zinc-700 px-3 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-brand-cyan"
              />
            </div>

            {error && (
              <p className="text-red-400 text-sm text-center">{error}</p>
            )}

            <button
              type="submit"
              className="w-full bg-brand-pink hover:bg-pink-600 text-white font-semibold rounded-lg py-3 transition-colors"
            >
              Publish
            </button>
          </form>
        )}

        {/* Step: Publishing spinner */}
        {step === 'publishing' && (
          <div className="flex flex-col items-center gap-4 py-12">
            <div className="w-10 h-10 border-2 border-brand-pink border-t-transparent rounded-full animate-spin" />
            <p className="text-zinc-300 text-sm">Publishing your video…</p>
          </div>
        )}

        {error && step === 'pick' && (
          <p className="text-red-400 text-sm text-center mt-4">{error}</p>
        )}
      </div>
    </main>
  );
}
