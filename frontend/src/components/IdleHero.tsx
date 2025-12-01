import { ChatInput } from "@/components/chat";

type IdleHeroProps = {
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  toggleListening: () => void;
};

export function IdleHero({
  inputValue,
  onInputChange,
  onSubmit,
  toggleListening,
}: IdleHeroProps) {
  return (
    <section className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-4xl flex-col items-center justify-center text-center">
      <p
        className="text-base uppercase tracking-[0.35em]"
        style={{ color: "var(--text-secondary)" }}
      >
        Moat Tutor
      </p>
      <h1
        className="mt-5 text-4xl font-semibold leading-tight md:text-5xl"
        style={{ color: "var(--text-primary)" }}
      >
        How can I help you?
      </h1>
      <p
        className="mt-3 max-w-2xl text-balance text-lg"
        style={{ color: "var(--text-secondary)" }}
      >
        Ask a question about any company and we'll connect chat with a
        financial dashboard, so every answer is backed by data.
      </p>

      <ChatInput
        value={inputValue}
        onChange={onInputChange}
        onSubmit={onSubmit}
        onToggleMic={toggleListening}
        variant="idle"
      />
    </section>
  );
}

