import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 p-6 text-slate-100">
      <h1 className="text-lg font-bold">Page not found</h1>
      <Link href="/" className="rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium hover:bg-sky-500">
        Back to Cairn
      </Link>
    </main>
  );
}
