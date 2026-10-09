"use client";

import { useEffect, useState } from "react";

import ConceptGraph from "@/components/ConceptGraph";
import { messageOf, type GraphOut } from "@/lib/api";
import { bootstrap } from "@/lib/session";

const NO_FLASH = new Set<string>();

export default function Home() {
  const [graph, setGraph] = useState<GraphOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    bootstrap(false)
      .then((b) => setGraph(b.graph))
      .catch((e) => setError(messageOf(e)));
  }, []);

  const mastery = Object.fromEntries((graph?.nodes ?? []).map((n) => [n.id, n.p_known]));

  return (
    <main className="min-h-screen bg-slate-950 p-4 text-slate-100">
      <h1 className="mb-3 text-lg font-bold">Cairn</h1>
      {error && <p className="mb-3 rounded bg-red-950 p-3 text-sm text-red-200">{error}</p>}
      {graph && (
        <div className="h-[80vh] overflow-hidden rounded-xl border border-slate-800">
          <ConceptGraph graph={graph} mastery={mastery} flash={NO_FLASH} />
        </div>
      )}
    </main>
  );
}
