import { useRef, useEffect } from "react";
import { MicIcon, SendIcon } from "@/components/icons";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onToggleMic: () => void;
  placeholder?: string;
  variant?: "idle" | "active";
};

export function ChatInput({
  value,
  onChange,
  onSubmit,
  onToggleMic,
  placeholder = "Ask any question",
  variant = "active",
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [value]);

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
          backgroundColor: "color-mix(in srgb, var(--surface) 70%, transparent)",
        }
      : {
          border: "1px solid var(--border)",
          backgroundColor: "color-mix(in srgb, var(--background) 80%, transparent)",
        };

  return (
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
        onClick={onToggleMic}
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border bg-transparent transition"
        style={{
          borderColor: "var(--border)",
          color: "var(--text-secondary)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "color-mix(in srgb, var(--border) 300%, transparent)";
          e.currentTarget.style.color = "var(--text-primary)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "var(--border)";
          e.currentTarget.style.color = "var(--text-secondary)";
        }}
        aria-label="Voice input (coming soon)"
        title="Voice input (coming soon)"
      >
        <MicIcon active={false} />
      </button>
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
      <button
        type="submit"
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-white transition"
        style={{
          backgroundColor: "var(--accent)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "color-mix(in srgb, var(--accent) 80%, black)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "var(--accent)";
        }}
        aria-label="Send message"
      >
        <SendIcon />
      </button>
    </form>
  );
}

