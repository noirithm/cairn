"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import HeatmapGrid from "@/components/HeatmapGrid";
import { getHeatmap, messageOf, type HeatmapOut } from "@/lib/api";
import { masteryColor } from "@/lib/color";

const REFRESH_MS = 10_000;

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-3">
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 text-sm font-semibold leading-snug">{value}</div>
    </div>
  );
}

export default function TeacherPage() {
  const [data, setData] = useState<HeatmapOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setData(await getHeatmap());
      setError(null);
    } catch (e) {
      setError(messageOf(e)); // keep showing the last good data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), REFRESH_MS);
    return () => clearInterval(timer);
  }, [load]);

  const diagnosedCount = data ? data.students.filter((s) => s.diagnosed !== null).length : 0;
  const top = data?.stats[0];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
        <div>
          <h1 className="text-lg font-bold tracking-tight">Cairn · Teacher view</h1>
          <p className="text-xs text-slate-400">
            Class-level misconception heatmap · refreshes every 10 s
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => void load()}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
          >
            Refresh
          </button>
          <Link
            href="/"
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
          >
            Student view
          </Link>
        </div>
      </header>

      {error && (
        <div className="m-4 flex items-center justify-between rounded-lg bg-red-950 p-3 text-sm text-red-200">
          <span>{error}</span>
          <button
            onClick={() => void load()}
            className="rounded border border-red-400/60 px-2 py-1 hover:bg-red-900"
          >
            Retry
          </button>
        </div>
      )}

      {loading && !data && <p className="p-5 text-sm text-slate-400">Loading…</p>}

      {data && data.n_students === 0 && (
        <p className="p-5 text-sm text-slate-300">
          No students have answered yet. Seed the demo class with{" "}
          <code className="rounded bg-slate-800 px-1">uv run python -m app.seed</code> (or restart the
          backend), then refresh.
        </p>
      )}

      {data && data.n_students > 0 && (
        <div className="grid gap-4 p-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <Stat label="Students" value={String(data.n_students)} />
              <Stat label="With a diagnosed misconception" value={String(diagnosedCount)} />
              <Stat label="Most common" value={top && top.diagnosed_count > 0 ? top.name : "None yet"} />
            </div>
            <HeatmapGrid data={data} />
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span>0%</span>
              <div
                className="h-2 w-40 rounded"
                style={{
                  background:
                    "linear-gradient(to right, rgba(245,158,11,0.06), rgba(245,158,11,1))",
                }}
              />
              <span>100% belief · white outline = diagnosed</span>
            </div>
          </div>

          <div className="space-y-4">
            <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Most common misconceptions
              </h2>
              <ul className="mt-3 space-y-3">
                {data.stats.map((s) => (
                  <li key={s.misconception_id}>
                    <div className="flex justify-between gap-2 text-xs">
                      <span>{s.name}</span>
                      <span className="shrink-0 text-slate-400">{s.diagnosed_count} diagnosed</span>
                    </div>
                    <div className="mt-1 h-2 rounded bg-slate-800">
                      <div
                        className="h-2 rounded bg-amber-500"
                        style={{ width: `${(s.diagnosed_count / data.n_students) * 100}%` }}
                      />
                    </div>
                    <div className="mt-0.5 text-[11px] text-slate-500">
                      {s.concept_id.replace(/_/g, " ")} · class average {Math.round(s.mean_p * 100)}%
                    </div>
                  </li>
                ))}
              </ul>
            </section>

            <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Class mastery by concept
              </h2>
              <ul className="mt-3 space-y-2">
                {data.concepts.map((c) => (
                  <li key={c.concept_id}>
                    <div className="flex justify-between text-xs">
                      <span>{c.name}</span>
                      <span className="text-slate-400">{Math.round(c.mean_p_known * 100)}%</span>
                    </div>
                    <div className="mt-1 h-2 rounded bg-slate-800">
                      <div
                        className="h-2 rounded"
                        style={{
                          width: `${c.mean_p_known * 100}%`,
                          backgroundColor: masteryColor(c.mean_p_known),
                        }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      )}
    </main>
  );
}
