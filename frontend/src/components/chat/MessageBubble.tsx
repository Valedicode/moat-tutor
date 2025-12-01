import { Message } from "@/types/chat";

type MessageBubbleProps = {
  message: Message;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className="flex flex-col gap-1 rounded-3xl border p-4"
      style={{
        borderColor: isUser
          ? "color-mix(in srgb, var(--accent) 20%, transparent)"
          : "var(--border-subtle)",
        backgroundColor: isUser
          ? "color-mix(in srgb, var(--background) 80%, transparent)"
          : "color-mix(in srgb, var(--surface-secondary) 50%, transparent)",
      }}
    >
      <div
        className="flex items-center justify-between text-xs uppercase tracking-[0.35em]"
        style={{ color: "var(--text-tertiary)" }}
      >
        <span>{isUser ? "You" : "Moat AI"}</span>
        <span>{message.timestamp}</span>
      </div>
      <p
        className="text-sm leading-relaxed"
        style={{ color: "var(--text-primary)" }}
      >
        {message.content}
      </p>
    </div>
  );
}

