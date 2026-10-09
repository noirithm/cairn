"use client";

import { useState, type FormEvent } from "react";

import {
  answerTransfer,
  createTransfer,
  messageOf,
  nextHint,
  type HintOut,
  type TransferOut,
  type TransferResultOut,
} from "@/lib/api";

const CONCEPTS: [string, string][] = [
  ["", "Weakest concept (auto)"],
  ["newton_2", "Newton second law"],
  ["weight", "Weight vs. mass"],
  ["normal", "Normal force"],
  ["friction", "Friction"],
  ["incline", "Inclined planes"],
  ["tension", "Tension"],
];

type Props = { sessionId: number; onMastery: (m: Record<string, number>) => void };

export default function TransferPanel({ sessionId, onMastery }: Props) {
  const [concept, setConcept] = useState("");
  const [problem, setProblem] = useState<TransferOut | null>(null);
  const [hints, setHints] = useState<HintOut[]>([]);
  const [value, setValue] = useState("");
  const [result, setResult] = useState<TransferResultOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const p = await createTransfer(sessionId, concept || undefined);
      setProblem(p);
      setHints([]);
      setResult(null);
      setValue("");
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setBusy(false);
    }
  }

  async function askHint() {
    if (!problem) return;
    setBusy(true);
    setError(null);
    try {
      const h = await nextHint(sessionId, problem.problem_id);
      setHints((prev) => [...prev, h]);
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setBusy(false);
    }
  }

  async function submit(ev: FormEvent) {
    ev.preventDefault();
    if (!problem || value.trim() === "") return;
    const n = Number(value);
    if (!Number.isFinite(n)) {
      setError("Enter a number.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await answerTransfer(sessionId, problem.problem_id, n);
      setResult(r);
      onMastery(r.mastery);
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setBusy(false);
    }
  }

  const solved = result?.correct === true;
  const remaining = problem ? problem.hints_available - hints.length : 0;

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      {error && <p className="mb-3 rounded bg-red-950 p-2 text-sm text-red-200">{error}</p>}

      {(!problem || solved) && (
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={concept}
            onChange={(e) => setConcept(e.target.value)}
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm"
          >
            {CONCEPTS.map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
          <button
            onClick={() => void start()}
            disabled={busy}
            className="rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
          >
            {problem ? "New problem" : "Start a transfer problem"}
          </button>
        </div>
      )}

      {problem && (
        <div className="mt-3">
          <p className="text-xs text-slate-400">
            {problem.concept_id.replace(/_/g, " ")} · answer verified with SymPy before you saw it
          </p>
          <p className="mt-2 text-sm leading-relaxed">{problem.text}</p>

          {hints.length > 0 && (
            <ol className="mt-3 space-y-1 text-sm text-amber-200">
              {hints.map((h) => (
                <li key={h.level}>
                  Hint {h.level}: {h.text}
                </li>
              ))}
            </ol>
          )}

          {!solved && (
            <form onSubmit={(ev) => void submit(ev)} className="mt-3 flex flex-wrap items-center gap-2">
              <input
                type="number"
                step="any"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Your answer"
                className="w-36 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm"
              />
              <span className="text-sm text-slate-300">{problem.unit}</span>
              <button
                type="submit"
                disabled={busy || value.trim() === ""}
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
              >
                Check
              </button>
              <button
                type="button"
                onClick={() => void askHint()}
                disabled={busy || remaining <= 0}
                className="rounded-md border border-slate-600 px-3 py-1.5 text-sm hover:bg-slate-800 disabled:opacity-50"
              >
                Hint ({remaining} left)
              </button>
            </form>
          )}

          {result && (
            <div className="mt-3 rounded-lg bg-slate-800 p-3 text-sm">
              <div className={`font-semibold ${result.correct ? "text-emerald-400" : "text-red-400"}`}>
                {result.correct ? "Correct" : "Not quite, try again"}
              </div>
              {result.solution && <p className="mt-1 text-slate-200">{result.solution}</p>}
              {result.trap && (
                <div className="mt-2 rounded border border-amber-500/60 bg-amber-500/10 p-2">
                  <div className="font-semibold text-amber-300">{result.trap.name}</div>
                  <p className="mt-1 text-slate-200">{result.trap.explanation}</p>
                </div>
              )}
              <p className="mt-2 text-xs text-slate-400">
                {result.mastery_updated
                  ? "Mastery updated on the graph."
                  : "No mastery change (already counted, or solved with heavy hints)."}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
