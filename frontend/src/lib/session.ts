import { ApiError, createSession, getGraph, type GraphOut } from "./api";

const SESSION_KEY = "cairn_session_id";

/** Resume the saved session if the backend still knows it, otherwise start a new student. */
export async function bootstrap(forceNew: boolean): Promise<{ sid: number; graph: GraphOut }> {
  const saved = forceNew ? null : Number(localStorage.getItem(SESSION_KEY)) || null;
  if (saved !== null) {
    try {
      return { sid: saved, graph: await getGraph(saved) };
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 404)) throw e; // stale id (e.g. DB was reset)
    }
  }
  const { session_id } = await createSession();
  localStorage.setItem(SESSION_KEY, String(session_id));
  return { sid: session_id, graph: await getGraph(session_id) };
}
