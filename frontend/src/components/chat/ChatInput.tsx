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
  const containerClass =
    variant === "idle"
      ? "mt-10 w-full max-w-2xl flex items-center gap-3 rounded-full p-2 backdrop-blur-2xl"
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
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="flex-1 bg-transparent text-base outline-none"
        style={{
          color: "var(--text-primary)",
        }}
      />
      <button
        type="submit"
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-white transition"
        style={{
          backgroundColor: "var(--button-primary)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "var(--button-primary-hover)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "var(--button-primary)";
        }}
        aria-label="Send message"
      >
        <SendIcon />
      </button>
    </form>
  );
}

