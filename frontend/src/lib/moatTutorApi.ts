export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type TranslationRequest = {
  file: File;
  model?: "whisper-1";
  response_format?: "json" | "text";
  prompt?: string;
  temperature?: number;
};

export type TranslationResponse = {
  success: boolean;
  text?: string | null;
  message: string;
};

export type MoatDimensionScore = {
  score: number;
  direction: "Strengthening" | "Stable" | "Weakening";
  confidence: "Low" | "Medium" | "High";
  rationale: string;
};

export type MoatAssessment = {
  switching_costs: MoatDimensionScore;
  network_effects: MoatDimensionScore;
  intangible_assets: MoatDimensionScore;
  cost_advantages: MoatDimensionScore;
  regulatory_barriers: MoatDimensionScore;
  ecosystem_lockin: MoatDimensionScore;
  overall_score: number;
  overall_rating: "Wide" | "Narrow" | "None";
  overall_confidence: "Low" | "Medium" | "High";
  assessment_period: string;
};

export type ParsedAnalysis = {
  ticker?: string;
  start_date?: string;
  end_date?: string;
  summary?: string;
  key_events?: string[];
  price_behavior?: string;
  moat_analysis?: unknown;
  plain_explanation?: string;
  concept_definitions?: Record<string, string>;
  learning_options?: unknown[];
  comprehension_questions?: string[];
  next_steps?: string[];
  moat_assessment?: MoatAssessment;
  raw_response?: string;
};

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

export type ChartDataResponse = {
  ticker: string;
  interval: string;
  interval_display: string;
  start_date: string;
  end_date: string;
  data_points: number;
  dates: string[];
  open: number[];
  high: number[];
  low: number[];
  close: number[];
  volume: number[];
  adj_close?: number[];
};

export type WindowPolicy = {
  output_mode: "rating" | "direction" | "signals";
  allow_rating: boolean;
  allow_scores: boolean;
  require_disclaimer: boolean;
};

export type TimeWindow = {
  label: string;
  window_type: "structural" | "phase" | "signal";
  start_date: string;
  end_date: string;
  duration_years: number;
  description: string;
  policy: WindowPolicy;
};

export type WindowedMoatReport = {
  window_label: string;
  window_type: "structural" | "phase" | "signal";
  start_date: string;
  end_date: string;
  duration_years: number;
  output_mode: "rating" | "direction" | "signals";
  allows_rating: boolean;
  requires_disclaimer: boolean;
  guidance: string;
  parsed_analysis: ParsedAnalysis;
};

export type MultiWindowReport = {
  ticker: string;
  generated_at: string;
  structural: WindowedMoatReport;
  phases: WindowedMoatReport[];
  synthesis?: string | null;
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
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  signal?: AbortSignal;
}): Promise<ChatResponse> {
  try {
    return await fetchJson<ChatResponse>("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: params.query,
        session_id: params.sessionId ?? undefined,
        ticker: params.ticker ?? undefined,
        start_date: params.startDate ?? undefined,
        end_date: params.endDate ?? undefined,
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

// For SSE streaming, we must call the backend directly (not through Next.js proxy)
// because Next.js rewrites buffer the entire response before forwarding.
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function chatStream(params: {
  query: string;
  sessionId?: string | null;
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  onEvent: (evt: StreamEvent) => void;
  signal?: AbortSignal;
}): Promise<void> {
  // Call backend directly to avoid Next.js proxy buffering
  const response = await fetch(`${BACKEND_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      session_id: params.sessionId ?? undefined,
      ticker: params.ticker ?? undefined,
      start_date: params.startDate ?? undefined,
      end_date: params.endDate ?? undefined,
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

export async function getChartData(params: {
  ticker: string;
  startDate?: string | null;
  endDate?: string | null;
  interval?: "auto" | "D" | "W" | "ME" | "M";
  signal?: AbortSignal;
}): Promise<ChartDataResponse> {
  try {
    const queryParams = new URLSearchParams();
    if (params.startDate) queryParams.set("start_date", params.startDate);
    if (params.endDate) queryParams.set("end_date", params.endDate);
    if (params.interval) queryParams.set("interval", params.interval);

    const url = `/api/v1/charts/${params.ticker}${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    
    return await fetchJson<ChartDataResponse>(url, {
      method: "GET",
      signal: params.signal,
    });
  } catch (error) {
    throw new Error(`Chart data request failed: ${toErrorMessage(error)}`);
  }
}

export async function analyzeMoat(params: {
  ticker: string;
  startDate: string;
  endDate: string;
  expertiseLevel?: "beginner" | "intermediate" | "professional";
  signal?: AbortSignal;
}): Promise<ParsedAnalysis> {
  try {
    return await fetchJson<ParsedAnalysis>("/api/v1/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticker: params.ticker,
        start_date: params.startDate,
        end_date: params.endDate,
        expertise_level: params.expertiseLevel || "intermediate",
      }),
      signal: params.signal,
    });
  } catch (error) {
    throw new Error(`Moat analysis request failed: ${toErrorMessage(error)}`);
  }
}

export async function translateAudio(
  request: TranslationRequest
): Promise<TranslationResponse> {
  const formData = new FormData();
  formData.append("file", request.file);

  if (request.model) {
    formData.append("model", request.model);
  }
  if (request.response_format) {
    formData.append("response_format", request.response_format);
  }
  if (request.prompt) {
    formData.append("prompt", request.prompt);
  }
  if (request.temperature !== undefined) {
    formData.append("temperature", request.temperature.toString());
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

    const response = await fetch("/api/audio/translate", {
      method: "POST",
      body: formData,
      signal: controller.signal,
      // Don't set Content-Type - browser sets it with boundary
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        (errorData as { detail?: string; message?: string }).detail ||
          (errorData as { detail?: string; message?: string }).message ||
          "Translation failed"
      );
    }

    return (await response.json()) as TranslationResponse;
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        throw new Error("Translation request timed out after 5 minutes");
      }
      throw new Error(`Translation failed: ${error.message}`);
    }
    throw new Error("Translation failed: Unknown error");
  }
}

// ============================================================================
// Windowed Moat Analysis API
// ============================================================================

export async function getAvailableWindows(signal?: AbortSignal): Promise<Record<string, TimeWindow>> {
  try {
    return await fetchJson<Record<string, TimeWindow>>("/api/v1/moat/windows", {
      method: "GET",
      signal,
    });
  } catch (error) {
    throw new Error(`Failed to fetch available windows: ${toErrorMessage(error)}`);
  }
}

export async function analyzeWithWindow(params: {
  ticker: string;
  windowLabel: string;
  signal?: AbortSignal;
}): Promise<WindowedMoatReport> {
  try {
    const queryParams = new URLSearchParams({
      ticker: params.ticker,
      window_label: params.windowLabel,
    });

    return await fetchJson<WindowedMoatReport>(
      `/api/v1/moat/analyze/window?${queryParams.toString()}`,
      {
        method: "POST",
        signal: params.signal,
      }
    );
  } catch (error) {
    throw new Error(`Windowed moat analysis failed: ${toErrorMessage(error)}`);
  }
}

export async function analyzeWithCustomWindow(params: {
  ticker: string;
  startDate: string;
  endDate: string;
  description?: string;
  signal?: AbortSignal;
}): Promise<WindowedMoatReport> {
  try {
    const queryParams = new URLSearchParams({
      ticker: params.ticker,
      start_date: params.startDate,
      end_date: params.endDate,
    });
    if (params.description) {
      queryParams.set("description", params.description);
    }

    return await fetchJson<WindowedMoatReport>(
      `/api/v1/moat/analyze/custom?${queryParams.toString()}`,
      {
        method: "POST",
        signal: params.signal,
      }
    );
  } catch (error) {
    throw new Error(`Custom window analysis failed: ${toErrorMessage(error)}`);
  }
}

export async function analyzeComprehensive(params: {
  ticker: string;
  includePhases?: boolean;
  signal?: AbortSignal;
}): Promise<MultiWindowReport> {
  try {
    const queryParams = new URLSearchParams({
      ticker: params.ticker,
      include_phases: String(params.includePhases ?? true),
    });

    return await fetchJson<MultiWindowReport>(
      `/api/v1/moat/analyze/comprehensive?${queryParams.toString()}`,
      {
        method: "POST",
        signal: params.signal,
      }
    );
  } catch (error) {
    throw new Error(`Comprehensive analysis failed: ${toErrorMessage(error)}`);
  }
}

// ============================================================================
// Overall Moat Score API (2015-2025 Full Analysis)
// ============================================================================

export type OverallMoatScore = {
  overall_score: number; // 0-5 scale
  rating: "Wide" | "Narrow" | "None";
  confidence: string;
  time_range: string;
  computed_at: string;
  factors: {
    network_effects: number;
    switching_costs: number;
    intangible_assets: number;
    cost_advantages: number;
    regulatory_barriers: number;
  };
  trend: "strengthening" | "stable" | "weakening";
  summary: string;
};

export async function getOverallMoatScore(params: {
  ticker: string;
  startDate?: string;
  endDate?: string;
  signal?: AbortSignal;
}): Promise<OverallMoatScore> {
  try {
    const { ticker, startDate, endDate } = params;
    
    // Build query params
    const queryParams = new URLSearchParams({ ticker });
    if (startDate) queryParams.append("start_date", startDate);
    if (endDate) queryParams.append("end_date", endDate);
    
    return await fetchJson<OverallMoatScore>(
      `/api/v1/moat/overall?${queryParams.toString()}`,
      {
        method: "GET",
        signal: params.signal,
      }
    );
  } catch (error) {
    throw new Error(`Failed to fetch overall moat score: ${toErrorMessage(error)}`);
  }
}
