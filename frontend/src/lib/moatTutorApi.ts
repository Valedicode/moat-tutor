export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type ParsedAnalysis = unknown;

export type ChatResponse = {
  message: ChatMessage;
  session_id: string;
  parsed?: ParsedAnalysis | null;
};

export type SessionInfo = {
  session_id: string;
  messages: ChatMessage[];
  created_at: string;
  last_activity: string;
};

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

async function fetchJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (response.ok) return (await response.json()) as T;

  let detail = `HTTP ${response.status}`;
  try {
    const body = (await response.json()) as { detail?: unknown; message?: unknown };
    if (body?.detail) detail = String(body.detail);
    else if (body?.message) detail = String(body.message);
  } catch {
    // ignore JSON parse failures
  }

  throw new Error(detail);
}

export async function chat(params: {
  query: string;
  sessionId?: string | null;
  signal?: AbortSignal;
}): Promise<ChatResponse> {
  try {
    return await fetchJson<ChatResponse>("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: params.query,
        session_id: params.sessionId ?? undefined,
      }),
      signal: params.signal,
    });
  } catch (error) {
    throw new Error(`Chat request failed: ${toErrorMessage(error)}`);
  }
}

export async function getChatHistory(params: {
  sessionId: string;
  signal?: AbortSignal;
}): Promise<SessionInfo> {
  try {
    return await fetchJson<SessionInfo>(`/api/v1/chat/history/${params.sessionId}`, {
      method: "GET",
      signal: params.signal,
    });
  } catch (error) {
    throw new Error(`History request failed: ${toErrorMessage(error)}`);
  }
}


