import dagre from "@dagrejs/dagre";

import type { GraphOut } from "./api";

export const NODE_W = 170;
export const NODE_H = 56;

/** Layered top-to-bottom layout: prerequisites sit above the concepts that depend on them. */
export function layout(graph: GraphOut): Record<string, { x: number; y: number }> {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 28, ranksep: 64 });
  graph.nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
  graph.edges.forEach((e) => g.setEdge(e.prereq, e.dependent));
  dagre.layout(g);

  const positions: Record<string, { x: number; y: number }> = {};
  graph.nodes.forEach((n) => {
    const p = g.node(n.id); // dagre returns the node centre
    positions[n.id] = { x: p.x - NODE_W / 2, y: p.y - NODE_H / 2 };
  });
  return positions;
}
