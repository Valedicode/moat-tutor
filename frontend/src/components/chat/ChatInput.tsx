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
      ? "mt-10 w-full max-w-2xl flex items-center gap-3 rounded-full border border-white/10 bg-[#181B21]/70 p-2 shadow-[0_25px_120px_rgba(0,0,0,0.55)] backdrop-blur-2xl"
      : "flex items-center gap-3 rounded-[24px] border border-white/10 bg-[#0F1115]/80 p-4";

  return (
    <form
      className={containerClass}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <button
        type="button"
        onClick={onToggleMic}
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-white/10 bg-transparent text-[#898D96] transition hover:border-white/30 hover:text-[#E1E3E6]"
        aria-label="Voice input (coming soon)"
        title="Voice input (coming soon)"
      >
        <MicIcon active={false} />
      </button>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="flex-1 bg-transparent text-base text-[#E1E3E6] outline-none placeholder:text-[#515761]"
      />
      <button
        type="submit"
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-[#7C3AED] transition hover:bg-[#9333EA]"
        aria-label="Send message"
      >
        <SendIcon />
      </button>
    </form>
  );
}

