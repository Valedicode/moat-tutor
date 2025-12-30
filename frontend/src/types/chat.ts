export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

// Audio translation types
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

