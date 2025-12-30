import { useRef, useEffect, useState, useCallback } from "react";
import { MicIcon, SendIcon, StopIcon } from "@/components/icons";
import { translateAudio, type TranslationRequest } from "@/lib/moatTutorApi";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  variant?: "idle" | "active";
};

// Audio visualization component
function AudioVisualization({ level }: { level: number }) {
  const circles = [0, 1, 2]; // 3 concentric circles

  return (
    <>
      {circles.map((index) => {
        // Scale calculation
        const baseScale = 1 + index * 0.12; // Base: 1.0, 1.12, 1.24
        const audioScale = level * (0.3 + index * 0.15); // Audio: level * (0.3, 0.45, 0.6)
        const finalScale = baseScale + audioScale;

        // Opacity calculation
        const baseOpacity = 0.12 - index * 0.03; // Base: 0.12, 0.09, 0.06
        const audioOpacity = level * (0.25 - index * 0.06); // Audio: level * (0.25, 0.19, 0.13)
        const finalOpacity = Math.max(
          0.05,
          Math.min(0.3, baseOpacity + audioOpacity)
        );

        return (
          <div
            key={index}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
            style={{
              width: `${24 + index * 8}px`, // 24px, 32px, 40px
              height: `${24 + index * 8}px`,
              backgroundColor: "var(--accent)",
              transform: `translate(-50%, -50%) scale(${finalScale})`,
              opacity: finalOpacity,
              transition: "transform 0.1s ease-out, opacity 0.1s ease-out",
            }}
          />
        );
      })}
    </>
  );
}

// Format time in MM:SS format
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  placeholder = "Ask any question",
  variant = "active",
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [value]);

  // Cleanup audio visualization
  const cleanupAudioVisualization = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setAudioLevel(0);
  }, []);

  // Setup audio visualization
  const setupAudioVisualization = useCallback(
    (stream: MediaStream) => {
      try {
        // Create AudioContext
        audioContextRef.current = new AudioContext();

        // Create AnalyserNode
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = 256; // Frequency bin count: 128
        analyserRef.current.smoothingTimeConstant = 0.3; // Lower = more responsive

        // Connect stream to analyser
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);

        // Create data array
        const bufferLength = analyserRef.current.frequencyBinCount; // 128
        const dataArray = new Uint8Array(bufferLength);

        // Animation loop
        const updateAudioLevel = () => {
          if (analyserRef.current && isRecording) {
            // Get frequency data (0-255 values)
            analyserRef.current.getByteFrequencyData(dataArray);

            // Calculate average volume
            const average =
              dataArray.reduce((a, b) => a + b, 0) / bufferLength;

            // Normalize to 0-1 range
            // Using /100 instead of /128 for better sensitivity
            const normalized = Math.min(average / 100, 1);

            setAudioLevel(normalized);

            // Continue loop
            animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
          }
        };

        // Start loop
        updateAudioLevel();
      } catch (err) {
        console.error("Error setting up audio visualization:", err);
      }
    },
    [isRecording]
  );

  // Process audio
  const processAudio = useCallback(
    async (blob: Blob) => {
      setIsProcessing(true);
      setError(null);

      try {
        // Convert Blob to File
        const file = new File([blob], "audio.webm", { type: blob.type });

        // Create translation request
        const request: TranslationRequest = {
          file,
          model: "whisper-1",
          response_format: "text",
        };

        // Call API
        const response = await translateAudio(request);

        // Insert text into input (trim to remove any trailing newlines)
        if (response.success && response.text) {
          const trimmedText = response.text.trim();
          onChange(trimmedText);
          setTimeout(() => {
            const textarea = textareaRef.current;
            if (textarea) {
              textarea.focus();
              // Move cursor to end of text
              textarea.setSelectionRange(trimmedText.length, trimmedText.length);
            }
          }, 100);
        } else {
          setError(response.message || "Translation failed");
        }
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : "Translation failed";
        setError(errorMsg);
      } finally {
        setIsProcessing(false);
      }
    },
    [onChange]
  );

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Setup audio visualization
      setupAudioVisualization(stream);

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Handle data chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle stop event (auto-process)
      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });

        // Cleanup
        streamRef.current?.getTracks().forEach((track) => track.stop());
        cleanupAudioVisualization();
        setIsRecording(false);
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
        setRecordingTime(0);

        // Auto-process audio
        await processAudio(blob);
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setError(null);

      // Start timer
      let time = 0;
      timerRef.current = setInterval(() => {
        time += 1;
        setRecordingTime(time);
      }, 1000);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Microphone access denied";
      setError(`Microphone access denied: ${errorMsg}`);
    }
  }, [setupAudioVisualization, cleanupAudioVisualization, processAudio]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      // onstop handler will automatically process the audio
    }
  }, [isRecording]);

  // Toggle recording
  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter = submit, Shift+Enter = new line
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  const containerClass =
    variant === "idle"
      ? "mt-10 w-full max-w-2xl flex items-center gap-3 rounded-[24px] p-2 backdrop-blur-2xl"
      : "flex items-center gap-3 rounded-[24px] p-4";

  const containerStyle =
    variant === "idle"
      ? {
          border: "1px solid var(--border)",
          backgroundColor:
            "color-mix(in srgb, var(--surface) 70%, transparent)",
        }
      : {
          border: "1px solid var(--border)",
          backgroundColor:
            "color-mix(in srgb, var(--background) 80%, transparent)",
        };

  return (
    <div>
      <form
        className={containerClass}
        style={containerStyle}
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <button
          type="button"
          onClick={toggleRecording}
          disabled={isProcessing}
          className="relative flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border transition"
          style={{
            borderColor: isRecording ? "transparent" : "var(--border)",
            backgroundColor: isRecording ? "#ef4444" : "transparent",
            color: isRecording ? "white" : "var(--text-secondary)",
            opacity: isProcessing ? 0.5 : 1,
            cursor: isProcessing ? "not-allowed" : "pointer",
          }}
          onMouseEnter={(e) => {
            if (!isRecording && !isProcessing) {
              e.currentTarget.style.borderColor =
                "color-mix(in srgb, var(--border) 300%, transparent)";
              e.currentTarget.style.color = "var(--text-primary)";
            }
          }}
          onMouseLeave={(e) => {
            if (!isRecording && !isProcessing) {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }
          }}
          aria-label={isRecording ? "Stop recording" : "Start voice input"}
          title={isRecording ? "Stop recording" : "Start voice input"}
        >
          {/* Icon */}
          <div className="relative z-10">
            {isRecording ? <StopIcon /> : <MicIcon active={false} />}
          </div>
        </button>

        {/* Recording timer badge */}
        {isRecording && (
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded-md"
            style={{ backgroundColor: "color-mix(in srgb, #ef4444 15%, transparent)" }}
          >
            <div
              className="h-1.5 w-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: "#ef4444" }}
            ></div>
            <span
              className="text-xs font-mono font-medium"
              style={{ color: "#ef4444" }}
            >
              {formatTime(recordingTime)}
            </span>
          </div>
        )}

        {/* Processing indicator */}
        {isProcessing && (
          <div className="flex items-center gap-3">
            <svg
              className="animate-spin h-5 w-5"
              style={{ color: "var(--accent)" }}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
              Translating to English...
            </span>
          </div>
        )}

        {/* Textarea (hidden when recording or processing) */}
        {!isRecording && !isProcessing && (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            className="flex-1 resize-none bg-transparent text-base outline-none py-2"
            style={{
              color: "var(--text-primary)",
              minHeight: "24px",
              maxHeight: "200px",
              lineHeight: "1.5",
            }}
          />
        )}

        {/* Send button (hidden when recording or processing) */}
        {!isRecording && !isProcessing && (
          <button
            type="submit"
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-white transition"
            style={{
              backgroundColor: "var(--accent)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor =
                "color-mix(in srgb, var(--accent) 80%, black)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "var(--accent)";
            }}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        )}
      </form>

      {/* Error message */}
      {error && (
        <div
          className="mt-2 text-sm px-4"
          style={{ color: "#ef4444" }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
