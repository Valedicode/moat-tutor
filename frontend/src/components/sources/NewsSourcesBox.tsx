"use client";

import { forwardRef, useCallback, useEffect, useRef, useState } from "react";
import { NewsSource } from "@/types/chat";
import { KeyNewsEvent } from "@/lib/moatTutorApi";

export type NewsMode = "referenced" | "key-news";

type NewsSourcesBoxProps = {
  mode: NewsMode;
  onModeChange: (mode: NewsMode) => void;
  referencedSources: NewsSource[];
  keyNews: KeyNewsEvent[];
  keyNewsLoading: boolean;
  keyNewsError: string | null;
  highlightedSourceId: string | null;
  hasTicker: boolean;
};

export function NewsSourcesBox({
  mode,
  onModeChange,
  referencedSources,
  keyNews,
  keyNewsLoading,
  keyNewsError,
  highlightedSourceId,
  hasTicker,
}: NewsSourcesBoxProps) {
  const itemRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [flashId, setFlashId] = useState<string | null>(null);

  useEffect(() => {
    if (!highlightedSourceId) return;

    const el = itemRefs.current.get(highlightedSourceId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      setFlashId(highlightedSourceId);
      const timer = setTimeout(() => setFlashId(null), 2500);
      return () => clearTimeout(timer);
    }
  }, [highlightedSourceId]);

  const setRef = useCallback(
    (id: string) => (el: HTMLDivElement | null) => {
      if (el) itemRefs.current.set(id, el);
      else itemRefs.current.delete(id);
    },
    [],
  );

  const hasReferenced = referencedSources.length > 0;

  return (
    <div className="flex flex-col gap-3">
      {/* Section Header */}
      <div className="flex items-center gap-2">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{ color: "var(--text-secondary)", flexShrink: 0 }}
        >
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <span
          className="text-xs uppercase tracking-wider font-semibold"
          style={{ color: "var(--text-secondary)" }}
        >
          News
        </span>
      </div>

      {/* Mode Tabs */}
      <div
        className="flex rounded-lg p-0.5"
        style={{
          backgroundColor: "color-mix(in srgb, var(--surface-secondary) 60%, transparent)",
        }}
      >
        <button
          type="button"
          onClick={() => onModeChange("referenced")}
          className="flex-1 text-[10px] uppercase tracking-wider font-medium py-1.5 px-2 rounded-md transition-all"
          style={{
            color:
              mode === "referenced"
                ? "var(--text-primary)"
                : "var(--text-tertiary)",
            backgroundColor:
              mode === "referenced"
                ? "var(--surface)"
                : "transparent",
          }}
        >
          Referenced{hasReferenced ? ` (${referencedSources.length})` : ""}
        </button>
        <button
          type="button"
          onClick={() => onModeChange("key-news")}
          className="flex-1 text-[10px] uppercase tracking-wider font-medium py-1.5 px-2 rounded-md transition-all"
          style={{
            color:
              mode === "key-news"
                ? "var(--text-primary)"
                : "var(--text-tertiary)",
            backgroundColor:
              mode === "key-news"
                ? "var(--surface)"
                : "transparent",
          }}
        >
          Key News
        </button>
      </div>

      {/* Content */}
      <div className="overflow-y-auto scrollbar-hide max-h-[40vh] space-y-2">
        {mode === "referenced" ? (
          hasReferenced ? (
            referencedSources.map((s, i) => (
              <SourceCard
                key={`ref-${s.passageId || i}`}
                ref={setRef(s.passageId || `ref-${i}`)}
                date={s.date}
                headline={s.headline}
                url={s.url}
                badge={s.similarity ? `rel ${s.similarity}` : undefined}
                isFlashing={flashId === (s.passageId || `ref-${i}`)}
                index={i + 1}
              />
            ))
          ) : (
            <EmptyState text="No sources referenced yet. Sources cited by the AI will appear here." />
          )
        ) : !hasTicker ? (
          <EmptyState text="Select a company and date range to see key news." />
        ) : keyNewsLoading ? (
          <LoadingState />
        ) : keyNewsError ? (
          <EmptyState text={keyNewsError} />
        ) : keyNews.length > 0 ? (
          keyNews.map((ev, i) => (
            <SourceCard
              key={`kn-${ev.passageId || i}`}
              ref={setRef(ev.passageId || `kn-${i}`)}
              date={ev.date}
              headline={ev.headline}
              url={ev.url}
              badge={ev.moatSource.replace(/_/g, " ")}
              isFlashing={flashId === (ev.passageId || `kn-${i}`)}
              index={i + 1}
            />
          ))
        ) : (
          <EmptyState text="No news articles found for this date range." />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

type SourceCardProps = {
  date: string;
  headline: string;
  url: string;
  badge?: string;
  isFlashing: boolean;
  index: number;
};

const SourceCard = forwardRef<HTMLDivElement, SourceCardProps>(
  function SourceCard({ date, headline, url, badge, isFlashing, index }, ref) {
    return (
      <div
        ref={ref}
        className="rounded-xl border p-2.5 transition-all duration-300"
        style={{
          borderColor: isFlashing
            ? "var(--accent)"
            : "var(--border-subtle)",
          backgroundColor: isFlashing
            ? "color-mix(in srgb, var(--accent) 8%, transparent)"
            : "color-mix(in srgb, var(--surface-secondary) 40%, transparent)",
          boxShadow: isFlashing
            ? "0 0 0 1px color-mix(in srgb, var(--accent) 30%, transparent)"
            : "none",
        }}
      >
        <div className="flex items-start gap-2">
          <span
            className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold"
            style={{
              backgroundColor: "color-mix(in srgb, var(--accent) 12%, transparent)",
              color: "var(--accent)",
            }}
          >
            {index}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 mb-0.5">
              <span
                className="text-[10px]"
                style={{ color: "var(--text-tertiary)" }}
              >
                {date}
              </span>
              {badge && (
                <span
                  className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded-full"
                  style={{
                    backgroundColor: "color-mix(in srgb, var(--accent) 10%, transparent)",
                    color: "var(--accent)",
                  }}
                >
                  {badge}
                </span>
              )}
            </div>
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="text-xs leading-snug hover:underline line-clamp-2"
                style={{ color: "var(--text-primary)" }}
              >
                {headline || url}
              </a>
            ) : (
              <span
                className="text-xs leading-snug line-clamp-2"
                style={{ color: "var(--text-primary)" }}
              >
                {headline || "Untitled"}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  },
);

function EmptyState({ text }: { text: string }) {
  return (
    <p
      className="text-xs text-center py-4 px-2 leading-relaxed"
      style={{ color: "var(--text-tertiary)" }}
    >
      {text}
    </p>
  );
}

function LoadingState() {
  return (
    <div className="space-y-2">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-xl border p-2.5 animate-pulse"
          style={{
            borderColor: "var(--border-subtle)",
            backgroundColor: "color-mix(in srgb, var(--surface-secondary) 40%, transparent)",
          }}
        >
          <div className="flex gap-2">
            <div
              className="w-5 h-5 rounded-full"
              style={{ backgroundColor: "var(--border)" }}
            />
            <div className="flex-1 space-y-1.5">
              <div
                className="h-2.5 rounded w-16"
                style={{ backgroundColor: "var(--border)" }}
              />
              <div
                className="h-3 rounded w-full"
                style={{ backgroundColor: "var(--border)" }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
