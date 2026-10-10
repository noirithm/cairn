"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 p-6 text-slate-100">
      <h1 className="text-lg font-bold">Something broke in the UI</h1>
      <p className="max-w-md text-center text-sm text-slate-400">{error.message}</p>
      <button
        onClick={reset}
        className="rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium hover:bg-sky-500"
      >
        Try again
      </button>
    </main>
  );
}
