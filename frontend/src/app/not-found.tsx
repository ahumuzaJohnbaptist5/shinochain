import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-black gap-4 px-4">
      <p className="text-7xl font-bold text-zinc-700">404</p>
      <h1 className="text-xl font-semibold text-white">Page not found</h1>
      <p className="text-zinc-400 text-sm text-center">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Link
        href="/"
        className="mt-2 px-5 py-2.5 bg-brand-pink hover:bg-pink-600 text-white rounded-lg text-sm font-semibold transition-colors"
      >
        Go home
      </Link>
    </main>
  );
}
