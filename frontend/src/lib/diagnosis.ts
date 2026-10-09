import type { DiagnosisEntry } from "./api";

export const DIAGNOSIS_THRESHOLD = 0.5; // mirrors DIAGNOSIS_THRESHOLD in the backend

/** The most likely misconception, once it passes the threshold. `entries` is sorted most-likely first. */
export function diagnosedFrom(entries: DiagnosisEntry[]): DiagnosisEntry | null {
  const top = entries[0];
  return top && top.id !== "correct" && top.p >= DIAGNOSIS_THRESHOLD ? top : null;
}
