const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function messageOf(e: unknown): string {
  return e instanceof ApiError ? e.message : "Something went wrong.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, `Cannot reach the backend at ${BASE}. Is it running?`);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---- types mirroring backend/app/schemas.py ----
export type Edge = { prereq: string; dependent: string; strength: number };
export type GraphNode = { id: string; name: string; section: string; p_known: number };
export type GraphOut = { unit: string; nodes: GraphNode[]; edges: Edge[] };

export type QuestionOut = {
  id: string;
  concept_id: string;
  prompt: string;
  options: { id: string; text: string }[];
};
export type NextQuestionOut = { question: QuestionOut | null; expected_gain: number };

export type DiagnosisEntry = { id: string; name: string; p: number; explanation: string | null };
export type DiagnosisOut = { diagnosis: DiagnosisEntry[]; entropy: number };
export type AnswerOut = {
  correct: boolean;
  explanation: string;
  mastery: Record<string, number>;
  diagnosis: DiagnosisEntry[];
  diagnosed: DiagnosisEntry | null;
};

export type TransferOut = {
  problem_id: number;
  concept_id: string;
  text: string;
  unit: string;
  hints_available: number;
  phrased_by: string;
};
export type HintOut = { level: number; text: string; remaining: number };
export type TransferResultOut = {
  correct: boolean;
  mastery_updated: boolean;
  hints_used: number;
  mastery: Record<string, number>;
  solution: string | null;
  trap: { misconception_id: string; name: string; explanation: string } | null;
};

// ---- endpoints ----
export const createSession = () => request<{ session_id: number }>("/sessions", { method: "POST" });
export const getGraph = (sid: number) => request<GraphOut>(`/sessions/${sid}/graph`);
export const getDiagnosis = (sid: number) => request<DiagnosisOut>(`/sessions/${sid}/diagnosis`);
export const nextQuestion = (sid: number) =>
  request<NextQuestionOut>(`/sessions/${sid}/next-question`);
export const submitAnswer = (sid: number, questionId: string, optionId: string) =>
  request<AnswerOut>(`/sessions/${sid}/answers`, {
    method: "POST",
    body: JSON.stringify({ question_id: questionId, option_id: optionId }),
  });
export const createTransfer = (sid: number, conceptId?: string) =>
  request<TransferOut>(`/sessions/${sid}/transfer`, {
    method: "POST",
    body: JSON.stringify(conceptId ? { concept_id: conceptId } : {}),
  });
export const nextHint = (sid: number, pid: number) =>
  request<HintOut>(`/sessions/${sid}/transfer/${pid}/hint`, { method: "POST" });
export const answerTransfer = (sid: number, pid: number, value: number) =>
  request<TransferResultOut>(`/sessions/${sid}/transfer/${pid}/answer`, {
    method: "POST",
    body: JSON.stringify({ value }),
  });

// ---- teacher view ----
export type HeatmapOut = {
  n_students: number;
  misconceptions: { id: string; name: string; concept_id: string }[];
  students: {
    id: number;
    name: string;
    is_simulated: boolean;
    answered: number;
    diagnosed: string | null;
  }[];
  cells: number[][]; // students x misconceptions, posterior probability
  stats: {
    misconception_id: string;
    name: string;
    concept_id: string;
    mean_p: number;
    diagnosed_count: number;
  }[];
  concepts: { concept_id: string; name: string; mean_p_known: number }[];
};
export const getHeatmap = () => request<HeatmapOut>("/teacher/heatmap");
