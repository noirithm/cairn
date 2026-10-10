"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import ConceptGraph from "@/components/ConceptGraph";
import DiagnosisCard from "@/components/DiagnosisCard";
import QuizPanel from "@/components/QuizPanel";
import TransferPanel from "@/components/TransferPanel";
import { getDiagnosis, messageOf, type AnswerOut, type DiagnosisEntry, type GraphOut } from "@/lib/api";
import { bootstrap } from "@/lib/session";

type Tab = "quiz" | "transfer";

export default function Home() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [graph, setGraph] = useState<GraphOut | null>(null);
  const [mastery, setMastery] = useState<Record<string, number>>({});
  const [flash, setFlash] = useState<Set<string>>(new Set());
  const [entries, setEntries] = useState<DiagnosisEntry[]>([]);
  const [tab, setTab] = useState<Tab>("quiz");
  const [error, setError] = useState<string | null>(null);

  const masteryRef = useRef<Record<string, number>>({});
  const flashTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const load = useCallback(async (forceNew: boolean) => {
    try {
      const { sid, graph } = await bootstrap(forceNew);
      const d = await getDiagnosis(sid);
      const m = Object.fromEntries(graph.nodes.map((n) => [n.id, n.p_known]));
      masteryRef.current = m;
      setSessionId(sid);
      setGraph(graph);
      setMastery(m);
      setFlash(new Set());
      setEntries(d.diagnosis);
      setError(null);
    } catch (e) {
      setError(messageOf(e));
    }
  }, []);

  useEffect(() => {
    void load(false);
  }, [load]);

  // Apply new mastery and briefly highlight the concepts that moved.
  const applyMastery = useCallback((next: Record<string, number>) => {
    const prev = masteryRef.current;
    const changed = new Set(Object.keys(next).filter((id) => Math.abs((prev[id] ?? 0) - next[id]) > 1e-9));
    masteryRef.current = next;
    setMastery(next);
    setFlash(changed);
    clearTimeout(flashTimer.current);
    flashTimer.current = setTimeout(() => setFlash(new Set()), 1800);
  }, []);

  const onQuizResult = useCallback(
    (r: AnswerOut) => {
      applyMastery(r.mastery);
      setEntries(r.diagnosis);
    },
    [applyMastery],
  );

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
        <div>
          <h1 className="text-lg font-bold tracking-tight">Cairn</h1>
          <p className="text-xs text-slate-400">Newton laws · concept-graph tutor</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/teacher"
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
          >
            Teacher view
          </Link>
          <button
            onClick={() => void load(true)}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
          >
            New student
          </button>
        </div>
      </header>

      {error && (
        <div className="m-4 flex items-center justify-between rounded-lg bg-red-950 p-3 text-sm text-red-200">
          <span>{error}</span>
          <button
            onClick={() => void load(false)}
            className="rounded border border-red-400/60 px-2 py-1 hover:bg-red-900"
          >
            Retry
          </button>
        </div>
      )}

      {!graph || sessionId === null ? (
        !error && <p className="p-5 text-sm text-slate-400">Loading…</p>
      ) : (
        <div className="grid gap-4 p-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
            <div className="h-[60vh] min-h-[380px] lg:h-[calc(100vh-170px)]">
              <ConceptGraph graph={graph} mastery={mastery} flash={flash} />
            </div>
            <div className="flex items-center gap-3 border-t border-slate-800 px-4 py-2 text-xs text-slate-400">
              <span>unsure</span>
              <div
                className="h-2 w-40 rounded"
                style={{
                  background:
                    "linear-gradient(to right, hsl(0 65% 38%), hsl(60 65% 38%), hsl(120 65% 38%))",
                }}
              />
              <span>mastered</span>
            </div>
          </section>

          <div className="flex flex-col gap-4">
            <div className="flex gap-2">
              {(["quiz", "transfer"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                    tab === t ? "bg-sky-600" : "border border-slate-700 hover:bg-slate-800"
                  }`}
                >
                  {t === "quiz" ? "Diagnostic quiz" : "Transfer problem"}
                </button>
              ))}
            </div>
            {/* Both stay mounted so switching tabs does not lose progress. */}
            <div className={tab === "quiz" ? "" : "hidden"}>
              <QuizPanel key={sessionId} sessionId={sessionId} onResult={onQuizResult} />
            </div>
            <div className={tab === "transfer" ? "" : "hidden"}>
              <TransferPanel key={sessionId} sessionId={sessionId} onMastery={applyMastery} />
            </div>
            <DiagnosisCard entries={entries} />
          </div>
        </div>
      )}
    </main>
  );
}
