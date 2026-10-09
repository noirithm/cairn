"use client";

import "@xyflow/react/dist/style.css";

import { useMemo } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";

import type { GraphOut } from "@/lib/api";
import { masteryColor } from "@/lib/color";
import { NODE_H, NODE_W, layout } from "@/lib/layout";

type ConceptData = { name: string; p: number; flash: boolean };
type ConceptNode = Node<ConceptData, "concept">;

const HANDLE_STYLE = { background: "#94a3b8", width: 8, height: 8 };

function ConceptNodeView({ data }: NodeProps<ConceptNode>) {
  return (
    <div
      style={{ width: NODE_W, height: NODE_H, backgroundColor: masteryColor(data.p) }}
      className={`flex flex-col items-center justify-center rounded-lg px-2 text-center text-white shadow transition-colors duration-500 ${
        data.flash ? "ring-4 ring-white" : "ring-1 ring-white/20"
      }`}
    >
      <Handle type="target" position={Position.Top} style={HANDLE_STYLE} />
      <div className="text-xs font-semibold leading-tight">{data.name}</div>
      <div className="text-[11px] opacity-90">{Math.round(data.p * 100)}%</div>
      <Handle type="source" position={Position.Bottom} style={HANDLE_STYLE} />
    </div>
  );
}

const nodeTypes = { concept: ConceptNodeView };

type Props = {
  graph: GraphOut;
  mastery: Record<string, number>;
  flash: Set<string>; // concepts whose mastery just changed
};

export default function ConceptGraph({ graph, mastery, flash }: Props) {
  // Positions depend only on graph structure, so they never jump when mastery changes.
  const positions = useMemo(() => layout(graph), [graph]);

  const nodes: ConceptNode[] = useMemo(
    () =>
      graph.nodes.map((n) => ({
        id: n.id,
        type: "concept" as const,
        position: positions[n.id],
        data: { name: n.name, p: mastery[n.id] ?? n.p_known, flash: flash.has(n.id) },
      })),
    [graph, positions, mastery, flash],
  );

  const edges: Edge[] = useMemo(
    () =>
      graph.edges.map((e) => ({
        id: `${e.prereq}->${e.dependent}`,
        source: e.prereq,
        target: e.dependent,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 1 + 2 * e.strength, opacity: 0.35 + 0.5 * e.strength },
      })),
    [graph],
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      colorMode="dark"
      fitView
      nodesDraggable={false}
      nodesConnectable={false}
    >
      <Background />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}
