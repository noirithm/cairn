/** Mastery 0..1 -> red (unsure) through amber to green (mastered). */
export function masteryColor(p: number): string {
  const clamped = Math.min(1, Math.max(0, p));
  return `hsl(${Math.round(clamped * 120)} 65% 38%)`;
}
