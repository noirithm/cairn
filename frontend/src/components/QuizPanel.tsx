"use client";

import { useEffect, useState } from "react";

import {
  messageOf,
  nextQuestion,
  submitAnswer,
  type AnswerOut,
  type QuestionOut,
} from "@/lib/api";

type Props = { sessionId: number; onResult: (r: AnswerOut) => void };

export default function QuizPanel({ sessionId, onResult }: Props) {
  const [question, setQuestion] = useState<QuestionOut | null>(null);
  const [gain, setGain] = useState(0);
  const [picked, setPicked] = useState<string | null>(null);
  const [result, setResult] = useState<AnswerOut | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    nextQuestion(sessionId)
      .then((r) => {
        if (cancelled) return;
        setQuestion(r.question);
        setGain(r.expected_gain);
      })
      .catch((e) => {
        if (!cancelled) setError(messageOf(e));
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  async function choose(optionId: string) {
    if (!question || result || busy) return;
    setBusy(true);
    setError(null);
    setPicked(optionId);
    try {
      const r = await submitAnswer(sessionId, question.id, optionId);
      setResult(r);
      onResult(r);
    } catch (e) {
      setError(messageOf(e));
      setPicked(null);
    } finally {
      setBusy(false);
    }
  }

  async function next() {
    setBusy(true);
    setError(null);
    try {
      const r = await nextQuestion(sessionId);
      setQuestion(r.question);
      setGain(r.expected_gain);
      setResult(null);
      setPicked(null);
    } catch (e) {
      setError(messageOf(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      {error && <p className="mb-3 rounded bg-red-950 p-2 text-sm text-red-200">{error}</p>}
      {busy && !question && !error && <p className="text-sm text-slate-400">Loading question…</p>}
      {!busy && !question && !error && (
        <p className="text-sm text-slate-300">
          You have answered every question. Try a transfer problem next.
        </p>
      )}
      {question && (
        <>
          <p className="text-xs text-slate-400">
            {question.concept_id.replace(/_/g, " ")} · picked for an expected information gain of{" "}
            {gain.toFixed(2)} bits
          </p>
          <h2 className="mt-2 text-base font-semibold leading-snug">{question.prompt}</h2>
          <ul className="mt-3 space-y-2">
            {question.options.map((o) => {
              let tone = "border-slate-700 bg-slate-800 hover:bg-slate-700";
              if (result && picked === o.id) {
                tone = result.correct
                  ? "border-emerald-500 bg-emerald-950"
                  : "border-red-500 bg-red-950";
              } else if (result) {
                tone = "border-slate-800 bg-slate-900 opacity-60";
              }
              return (
                <li key={o.id}>
                  <button
                    disabled={busy || result !== null}
                    onClick={() => void choose(o.id)}
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${tone}`}
                  >
                    {o.text}
                  </button>
                </li>
              );
            })}
          </ul>
          {result && (
            <div className="mt-4 rounded-lg bg-slate-800 p-3 text-sm">
              <div className={`font-semibold ${result.correct ? "text-emerald-400" : "text-red-400"}`}>
                {result.correct ? "Correct" : "Not quite"}
              </div>
              <p className="mt-1 text-slate-200">{result.explanation}</p>
              <button
                onClick={() => void next()}
                disabled={busy}
                className="mt-3 rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
              >
                Next question
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
