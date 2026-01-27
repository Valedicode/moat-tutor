"use client";

import { useState } from "react";
import { Message } from "@/types/chat";
import { ChatInput, MessageBubble } from "@/components/chat";
import { StudioPanel } from "@/components/StudioPanel";
import { MoatAssessment } from "@/lib/moatTutorApi";
import { CompanySelectorCompact } from "@/components/CompanySelectorCompact";
import { DateRangePickerCompact } from "@/components/DateRangePickerCompact";

type ThreeColumnLayoutProps = {
  messages: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (value?: string) => void;
  chatScrollRef: React.MutableRefObject<HTMLDivElement | null>;
  ticker?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  moatAssessment?: MoatAssessment | null;
  selectedCompanyId: string | null;
  onCompanyChange: (id: string | null) => void;
  startYear: number;
  endYear: number;
  onStartYearChange: (year: number) => void;
  onEndYearChange: (year: number) => void;
};

export function ThreeColumnLayout({
  messages,
  inputValue,
  onInputChange,
  onSubmit,
  chatScrollRef,
  ticker,
  startDate,
  endDate,
  moatAssessment,
  selectedCompanyId,
  onCompanyChange,
  startYear,
  endYear,
  onStartYearChange,
  onEndYearChange,
}: ThreeColumnLayoutProps) {
  const [leftPanelOpen, setLeftPanelOpen] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  return (
    <div className="mx-auto flex w-full gap-4 mt-16 sm:mt-20" style={{ maxWidth: "100%", height: "calc(100vh - 8rem)" }}>
      {/* LEFT PANEL - Sources */}
      <aside
        className={`flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden`}
        style={{
          width: leftPanelOpen ? "320px" : "0px",
        }}
      >
        {leftPanelOpen && (
          <div
            className="h-full flex flex-col rounded-[28px] border p-6 backdrop-blur-3xl animate-in fade-in slide-in-from-left-4 duration-300"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "color-mix(in srgb, var(--surface) 85%, transparent)",
            }}
          >
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h3
                  className="text-xs uppercase tracking-[0.3em] font-semibold"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Sources
                </h3>
                <button
                  onClick={() => setLeftPanelOpen(false)}
                  className="p-1 rounded-lg hover:bg-opacity-20 transition-all"
                  style={{ color: "var(--text-secondary)" }}
                  title="Close sources panel"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Select company and date range
              </p>
            </div>

            {/* Company Selector */}
            <div className="mb-6 flex-shrink-0">
              <label
                className="block text-xs uppercase tracking-wider mb-2 font-semibold"
                style={{ color: "var(--text-secondary)" }}
              >
                Company
              </label>
              <CompanySelectorCompact
                selectedCompanyId={selectedCompanyId}
                onCompanyChange={onCompanyChange}
              />
            </div>

            {/* Date Range */}
            <div className="flex-shrink-0">
              <label
                className="block text-xs uppercase tracking-wider mb-2 font-semibold"
                style={{ color: "var(--text-secondary)" }}
              >
                Date Range
              </label>
              <DateRangePickerCompact
                startYear={startYear}
                endYear={endYear}
                onStartYearChange={onStartYearChange}
                onEndYearChange={onEndYearChange}
              />
            </div>

            {/* Selected Info Summary */}
            {ticker && (
              <div
                className="mt-auto pt-4 border-t text-xs"
                style={{
                  borderColor: "var(--border)",
                  color: "var(--text-tertiary)",
                }}
              >
                <div className="space-y-1">
                  <p>
                    <span className="font-semibold" style={{ color: "var(--text-secondary)" }}>
                      {ticker}
                    </span>
                  </p>
                  <p>
                    {startYear} - {endYear}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* CENTER PANEL - Chat */}
      <main className="flex-1 flex flex-col min-w-0">
        <div
          className="h-full flex flex-col rounded-[28px] border p-6 backdrop-blur-3xl"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "color-mix(in srgb, var(--surface) 75%, transparent)",
          }}
        >
          {/* Header with toggle buttons */}
          <div className="flex items-center gap-3 mb-6">
            {/* Left Panel Toggle */}
            <button
              onClick={() => setLeftPanelOpen(!leftPanelOpen)}
              className={`p-2 rounded-lg transition-all ${leftPanelOpen ? "bg-opacity-10" : ""}`}
              style={{
                color: leftPanelOpen ? "var(--accent)" : "var(--text-secondary)",
                backgroundColor: leftPanelOpen ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
              }}
              title="Toggle sources panel"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </button>

            {/* Chat Title */}
            <div className="flex-1">
              <p
                className="text-xs uppercase tracking-[0.3em]"
                style={{ color: "var(--text-secondary)" }}
              >
                Conversation
              </p>
              <h2
                className="mt-1 text-xl font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                AI Research Chat
              </h2>
            </div>

            {/* Right Panel Toggle */}
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className={`p-2 rounded-lg transition-all ${rightPanelOpen ? "bg-opacity-10" : ""}`}
              style={{
                color: rightPanelOpen ? "var(--accent)" : "var(--text-secondary)",
                backgroundColor: rightPanelOpen ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
              }}
              title="Toggle studio panel"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
            </button>
          </div>

          {/* Chat Messages */}
          <div
            ref={chatScrollRef}
            className="scrollbar-hide flex-1 min-h-0 space-y-4 overflow-y-auto pr-2"
          >
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>

          {/* Chat Input */}
          <div className="mt-6 flex-shrink-0">
            <ChatInput
              value={inputValue}
              onChange={onInputChange}
              onSubmit={() => onSubmit()}
              variant="active"
            />
          </div>
        </div>
      </main>

      {/* RIGHT PANEL - Studio */}
      <aside
        className={`flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden`}
        style={{
          width: rightPanelOpen ? "480px" : "0px",
        }}
      >
        {rightPanelOpen && (
          <div
            className="h-full flex flex-col rounded-[28px] border p-6 backdrop-blur-3xl animate-in fade-in slide-in-from-right-4 duration-300"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "color-mix(in srgb, var(--surface) 85%, transparent)",
            }}
          >
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h3
                  className="text-xs uppercase tracking-[0.3em] font-semibold"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Studio
                </h3>
                <button
                  onClick={() => setRightPanelOpen(false)}
                  className="p-1 rounded-lg hover:bg-opacity-20 transition-all"
                  style={{ color: "var(--text-secondary)" }}
                  title="Close studio panel"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Visualizations and analytics
              </p>
            </div>

            {/* Studio Content */}
            <div className="flex-1 min-h-0">
              <StudioPanel
                ticker={ticker}
                startDate={startDate}
                endDate={endDate}
                moatAssessment={moatAssessment}
                startYear={startYear}
                endYear={endYear}
              />
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
