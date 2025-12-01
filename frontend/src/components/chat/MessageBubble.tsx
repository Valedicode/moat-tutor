import { Message } from "@/types/chat";

type MessageBubbleProps = {
  message: Message;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex flex-col gap-1 rounded-3xl border p-4 ${
        isUser
          ? "border-[#00E0FF]/20 bg-[#0F1115]/80"
          : "border-white/5 bg-white/[0.08]"
      }`}
    >
      <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-[#666b74]">
        <span>{isUser ? "You" : "Moat AI"}</span>
        <span>{message.timestamp}</span>
      </div>
      <p className="text-sm leading-relaxed text-[#E1E3E6]">
        {message.content}
      </p>
    </div>
  );
}

