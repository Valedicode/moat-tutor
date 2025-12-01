import { Message } from "@/types/chat";
import { ChatInput, MessageBubble } from "@/components/chat";
import { MoatDashboard } from "@/components/dashboard";

type ActiveShellProps = {
  messages: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (value?: string) => void;
  chatScrollRef: React.MutableRefObject<HTMLDivElement | null>;
  toggleListening: () => void;
};

export function ActiveShell({
  messages,
  inputValue,
  onInputChange,
  onSubmit,
  chatScrollRef,
  toggleListening,
}: ActiveShellProps) {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 lg:flex-row">
      <section
        className="flex min-h-[75vh] basis-full flex-col rounded-[36px] border p-6 backdrop-blur-3xl transition-all duration-500 lg:basis-[32%]"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "color-mix(in srgb, var(--surface) 75%, transparent)",
        }}
      >
        <div
          className="rounded-[28px] border p-5"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "var(--border-subtle)",
          }}
        >
          <p
            className="text-xs uppercase tracking-[0.4em]"
            style={{ color: "var(--text-secondary)" }}
          >
            Conversation
          </p>
          <h2
            className="mt-3 text-2xl font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            AI Research Chat
          </h2>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Your questions drive the moat analysis. Each answer triggers a new
            panel on the right.
          </p>
        </div>

        <div
          ref={chatScrollRef}
          className="scrollbar-hide mt-6 flex-1 space-y-4 overflow-y-auto pr-2"
        >
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>

        <div className="mt-6">
          <ChatInput
            value={inputValue}
            onChange={onInputChange}
            onSubmit={() => onSubmit()}
            onToggleMic={toggleListening}
            variant="active"
          />
        </div>
      </section>

      <section className="flex flex-1">
        <MoatDashboard />
      </section>
    </div>
  );
}

