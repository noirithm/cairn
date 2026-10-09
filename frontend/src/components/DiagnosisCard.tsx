import type { DiagnosisEntry } from "@/lib/api";
import { diagnosedFrom } from "@/lib/diagnosis";

export default function DiagnosisCard({ entries }: { entries: DiagnosisEntry[] }) {
  const diagnosed = diagnosedFrom(entries);
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        What Cairn thinks
      </h2>
      {diagnosed && (
        <div className="mt-3 rounded-lg border border-amber-500/60 bg-amber-500/10 p-3">
          <div className="text-xs font-semibold uppercase text-amber-300">
            Misconception diagnosed
          </div>
          <div className="mt-1 font-semibold">{diagnosed.name}</div>
          <p className="mt-1 text-sm text-slate-200">{diagnosed.explanation}</p>
        </div>
      )}
      <ul className="mt-3 space-y-2">
        {entries.slice(0, 4).map((e) => (
          <li key={e.id}>
            <div className="flex justify-between text-xs text-slate-300">
              <span>{e.name}</span>
              <span>{Math.round(e.p * 100)}%</span>
            </div>
            <div className="mt-1 h-2 rounded bg-slate-800">
              <div
                className={`h-2 rounded ${e.id === "correct" ? "bg-emerald-500" : "bg-amber-500"}`}
                style={{ width: `${Math.round(e.p * 100)}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
