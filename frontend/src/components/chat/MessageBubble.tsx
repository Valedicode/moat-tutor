import { useMemo, useState } from "react";
import { Message } from "@/types/chat";

type MessageBubbleProps = {
  message: Message;
};

type Source = {
  date: string;
  headline: string;
  url: string;
  similarity: string;
  passageId: string;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  const { mainText, sources } = useMemo(() => {
    const text = message.content ?? "";
    const start = text.indexOf("[SOURCES_START]");
    const end = text.indexOf("[SOURCES_END]");

    if (start === -1 || end === -1 || end <= start) {
      return { mainText: text, sources: [] as Source[] };
    }

    const before = text.slice(0, start).trimEnd();
    const block = text.slice(start + "[SOURCES_START]".length, end).trim();
    const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);

    const parsed = lines.map((line) => {
      // idx|date|headline|url|similarity|passage_id
      const [, date, headline, url, similarity, passageId] = line.split("|");
      return {
        date: date ?? "",
        headline: headline ?? "",
        url: (url ?? "").replace("%7C", "|"),
        similarity: similarity ?? "",
        passageId: passageId ?? "",
      };
    });

    return { mainText: before, sources: parsed };
  }, [message.content]);

  const [showSources, setShowSources] = useState(false);

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
        className="text-sm leading-relaxed whitespace-pre-wrap"
        style={{ color: "var(--text-primary)" }}
      >
        {mainText}
      </p>

      {!isUser && sources.length > 0 && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setShowSources((v) => !v)}
            className="text-xs underline transition-opacity hover:opacity-70"
            style={{ color: "var(--text-secondary)" }}
          >
            {showSources ? "Hide sources" : `Show sources (${sources.length})`}
          </button>

          {showSources && (
            <div className="mt-2 space-y-2">
              {sources.map((s, i) => (
                <div
                  key={`${s.url}-${i}`}
                  className="text-xs"
                  style={{ color: "var(--text-secondary)" }}
                >
                  <div>
                    <span style={{ color: "var(--text-tertiary)" }}>{s.date}</span>{" "}
                    {s.similarity ? (
                      <span style={{ color: "var(--text-tertiary)" }}>
                        (rel {s.similarity})
                      </span>
                    ) : null}
                  </div>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:opacity-80"
                    style={{ color: "var(--accent)" }}
                  >
                    {s.headline || s.url}
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

