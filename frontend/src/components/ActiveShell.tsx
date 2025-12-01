import { Message } from "@/types/chat";
import { ChatInput, MessageBubble } from "@/components/chat";

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
      <section className="flex min-h-[75vh] basis-full flex-col rounded-[36px] border border-white/10 bg-[#181B21]/75 p-6 shadow-[0_30px_140px_rgba(0,0,0,0.55)] backdrop-blur-3xl transition-all duration-500 lg:basis-[32%]">
        <div className="rounded-[28px] border border-white/10 bg-white/5 p-5">
          <p className="text-xs uppercase tracking-[0.4em] text-[#898D96]">
            Conversation
          </p>
          <h2 className="mt-3 text-2xl font-semibold">AI Research Chat</h2>
          <p className="mt-1 text-sm text-[#898D96]">
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

      <section className="flex flex-1 items-center justify-center rounded-[36px] border border-dashed border-white/15 bg-white/5 text-center text-sm text-[#616773]">
        The Moat Dashboard (70%) will be integrated in the next step.
      </section>
    </div>
  );
}

