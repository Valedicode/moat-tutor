import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Message } from "@/types/chat";
import { NewsSource } from "@/types/chat";
import { parseMessageSources } from "@/utils/sourceParsing";

type MessageBubbleProps = {
  message: Message;
  onCitationClick?: (passageId: string) => void;
};

type CitationChipProps = {
  index: number;
  source: NewsSource;
  onCitationClick?: (passageId: string) => void;
};

function CitationChip({ index, source, onCitationClick }: CitationChipProps) {
  return (
    <button
      type="button"
      onClick={() => {
        const id = source.passageId || `ref-${index - 1}`;
        if (onCitationClick) onCitationClick(id);
      }}
      className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold transition-all hover:scale-110 align-middle relative -top-px mx-0.5"
      style={{
        backgroundColor: "color-mix(in srgb, var(--accent) 15%, transparent)",
        color: "var(--accent)",
      }}
      title={source.headline || source.url || `Source ${index}`}
    >
      {index}
    </button>
  );
}

function renderInlineText(
  text: string,
  sources: NewsSource[],
  onCitationClick?: (passageId: string) => void,
): ReactNode[] {
  // Split on [N] markers, keeping the delimiters
  const parts = text.split(/(\[\d+\])/);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const n = parseInt(match[1], 10);
      const source = sources[n - 1];
      if (source) {
        return (
          <CitationChip
            key={`chip-${i}`}
            index={n}
            source={source}
            onCitationClick={onCitationClick}
          />
        );
      }
      // No matching source — render as plain text
      return <span key={`plain-${i}`}>{part}</span>;
    }
    return <span key={`text-${i}`}>{part}</span>;
  });
}

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === "user";

  const { mainText, sources } = useMemo(
    () => parseMessageSources(message.content ?? ""),
    [message.content],
  );

  const [showSources, setShowSources] = useState(false);

  const hasInlineMarkers = !isUser && sources.length > 0 && /\[\d+\]/.test(mainText);

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
        {hasInlineMarkers
          ? renderInlineText(mainText, sources, onCitationClick)
          : mainText}
      </p>

      {!isUser && sources.length > 0 && (
        <div className="mt-2">
          {/* When no inline markers, show chips in a grouped row as fallback */}
          {!hasInlineMarkers && (
            <div className="flex flex-wrap items-center gap-1.5">
              <span
                className="text-[10px] uppercase tracking-wider mr-1"
                style={{ color: "var(--text-tertiary)" }}
              >
                Sources
              </span>
              {sources.map((s, i) => (
                <CitationChip
                  key={`chip-${s.passageId || i}`}
                  index={i + 1}
                  source={s}
                  onCitationClick={onCitationClick}
                />
              ))}
            </div>
          )}

          {/* Expand/collapse toggle */}
          <button
            type="button"
            onClick={() => setShowSources((v) => !v)}
            className="mt-1 text-[10px] transition-opacity hover:opacity-70"
            style={{ color: "var(--text-tertiary)" }}
          >
            {showSources ? "hide sources" : "show sources"}
          </button>

          {/* Expandable detail list */}
          {showSources && (
            <div className="mt-2 space-y-2">
              {sources.map((s, i) => (
                <div
                  key={`${s.url}-${i}`}
                  className="text-xs"
                  style={{ color: "var(--text-secondary)" }}
                >
                  <div>
                    <span
                      className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[8px] font-bold mr-1"
                      style={{
                        backgroundColor: "color-mix(in srgb, var(--accent) 12%, transparent)",
                        color: "var(--accent)",
                      }}
                    >
                      {i + 1}
                    </span>
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

