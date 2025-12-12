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

export type StreamEvent =
  | { event: "meta"; data: { session_id: string; message_id: string } }
  | { event: "delta"; data: { delta: string } }
  | { event: "done"; data: ChatResponse }
  | { event: "error"; data: { error: string } };

export async function chatStream(params: {
  query: string;
  sessionId?: string | null;
  onEvent: (evt: StreamEvent) => void;
  signal?: AbortSignal;
}): Promise<void> {
  const response = await fetch("/api/v1/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      session_id: params.sessionId ?? undefined,
    }),
    signal: params.signal,
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => `HTTP ${response.status}`);
    throw new Error(`Stream request failed: ${detail}`);
  }

  if (!response.body) {
    throw new Error("No response body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  function parseSseFrame(frame: string): { event?: string; data?: string } {
    const lines = frame.split("\n");
    let event: string | undefined;
    const dataLines: string[] = [];
    for (const line of lines) {
      const trimmed = line.trimEnd();
      if (trimmed.startsWith("event:")) {
        event = trimmed.slice("event:".length).trim();
      } else if (trimmed.startsWith("data:")) {
        dataLines.push(trimmed.slice("data:".length).trim());
      }
    }
    return { event, data: dataLines.length ? dataLines.join("\n") : undefined };
  }

  function parseSseFrames(buffer: string): { frames: string[]; rest: string } {
    const parts = buffer.split("\n\n");
    if (parts.length === 1) return { frames: [], rest: buffer };
    const rest = parts.pop() ?? "";
    return { frames: parts, rest };
  }

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const { frames, rest } = parseSseFrames(buffer);
    buffer = rest;

    for (const frame of frames) {
      const { event, data } = parseSseFrame(frame);
      if (!event || !data) continue;

      try {
        const parsed = JSON.parse(data) as unknown;

        if (event === "meta") {
          params.onEvent({
            event: "meta",
            data: parsed as { session_id: string; message_id: string },
          });
        } else if (event === "delta") {
          params.onEvent({
            event: "delta",
            data: parsed as { delta: string },
          });
        } else if (event === "done") {
          params.onEvent({
            event: "done",
            data: parsed as ChatResponse,
          });
        } else if (event === "error") {
          params.onEvent({
            event: "error",
            data: parsed as { error: string },
          });
        }
      } catch (e) {
        console.warn("Failed to parse SSE frame:", e);
      }
    }
  }
}

