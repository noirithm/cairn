import type { HeatmapOut } from "@/lib/api";

/** Posterior probability -> amber, from nearly transparent to solid. */
function heat(p: number): string {
  const clamped = Math.min(1, Math.max(0, p));
  return `rgba(245, 158, 11, ${(0.06 + 0.94 * clamped).toFixed(2)})`;
}

export default function HeatmapGrid({ data }: { data: HeatmapOut }) {
  return (
    <div className="max-h-[70vh] overflow-auto rounded-xl border border-slate-800">
      <table className="min-w-full border-separate border-spacing-0 text-xs">
        <thead>
          <tr>
            <th className="sticky left-0 top-0 z-30 bg-slate-900 px-3 py-2 text-left font-semibold">
              Student
            </th>
            {data.misconceptions.map((m) => (
              <th
                key={m.id}
                title={m.name}
                className="sticky top-0 z-20 w-24 min-w-[6rem] bg-slate-900 px-2 py-2 text-left align-bottom font-medium leading-tight text-slate-300"
              >
                {m.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.students.map((s, i) => (
            <tr key={s.id}>
              <td className="sticky left-0 z-10 whitespace-nowrap bg-slate-950 px-3 py-1.5 font-medium">
                {s.name}
                {!s.is_simulated && (
                  <span className="ml-2 rounded bg-sky-600 px-1.5 py-0.5 text-[10px]">live</span>
                )}
              </td>
              {data.cells[i].map((p, j) => {
                const m = data.misconceptions[j];
                const diagnosed = s.diagnosed === m.id;
                return (
                  <td
                    key={m.id}
                    title={`${s.name} · ${m.name}: ${Math.round(p * 100)}%`}
                    style={{ backgroundColor: heat(p) }}
                    className={`h-8 text-center ${
                      diagnosed ? "font-bold text-white ring-2 ring-inset ring-white" : "text-slate-100"
                    }`}
                  >
                    {Math.round(p * 100)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
