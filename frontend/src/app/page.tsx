"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Message } from "@/types/chat";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ActiveShell } from "@/components/ActiveShell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Logo } from "@/components/Logo";
import { nowStamp } from "@/utils/date";
import { chat, chatStream, type StreamEvent, type MoatAssessment } from "@/lib/moatTutorApi";
import { availableCompanies } from "@/constants/companies";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [startYear, setStartYear] = useState<number>(2015);
  const [endYear, setEndYear] = useState<number>(2015);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);
  const [moatAssessment, setMoatAssessment] = useState<MoatAssessment | null>(null);

  const isActiveSession = messages.length > 0;

  // Derive ticker and date range from selection
  const selectedCompany = selectedCompanyId
    ? availableCompanies.find((c) => c.id === selectedCompanyId)
    : null;
  const ticker = selectedCompany?.ticker ?? null;
  const startDate = ticker ? `${startYear}-01-01` : null;
  const endDate = ticker ? `${endYear}-12-31` : null;

  useEffect(() => {
    if (!chatScrollRef.current) return;
    chatScrollRef.current.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const handleSend = async (value?: string) => {
    if (isSending) return;
    const text = (value ?? inputValue).trim();
    if (!text) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: nowStamp(),
    };

    setInputValue("");

    const placeholderId = crypto.randomUUID();
    const assistantPlaceholder: Message = {
      id: placeholderId,
      role: "assistant",
      content: "Thinking…",
      timestamp: nowStamp(),
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setIsSending(true);

    try {
      // Prefer streaming; fall back to non-streaming if it fails.
      let accumulated = "";
      await chatStream({
        query: text,
        sessionId,
        ticker,
        startDate,
        endDate,
        onEvent: (evt: StreamEvent) => {
          if (evt.event === "meta") {
            setSessionId(evt.data.session_id);
          } else if (evt.event === "delta") {
            accumulated += evt.data.delta;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === placeholderId ? { ...msg, content: accumulated } : msg,
              ),
            );
          } else if (evt.event === "done") {
            setSessionId(evt.data.session_id);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === placeholderId ? evt.data.message : msg,
              ),
            );
            // Capture moat assessment from parsed response
            if (evt.data.parsed?.moat_assessment) {
              setMoatAssessment(evt.data.parsed.moat_assessment);
              // Also cache it in localStorage for persistence
              if (ticker && startDate && endDate) {
                const cacheKey = `moat_${ticker}_${startDate}_${endDate}`;
                try {
                  localStorage.setItem(cacheKey, JSON.stringify({
                    assessment: evt.data.parsed.moat_assessment,
                    timestamp: Date.now(),
                  }));
                } catch (e) {
                  console.warn("Failed to cache moat assessment:", e);
                }
              }
            }
          } else if (evt.event === "error") {
            throw new Error(evt.data.error);
          }
        },
      });
    } catch (error) {
      try {
        const result = await chat({ query: text, sessionId, ticker, startDate, endDate });
        setSessionId(result.session_id);
        setMessages((prev) =>
          prev.map((msg) => (msg.id === placeholderId ? result.message : msg)),
        );
        // Capture moat assessment from parsed response
        if (result.parsed?.moat_assessment) {
          setMoatAssessment(result.parsed.moat_assessment);
        }
      } catch (fallbackError) {
        const message =
          fallbackError instanceof Error
            ? fallbackError.message
            : "Unknown error occurred";
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === placeholderId
              ? {
                  ...msg,
                  content: `Sorry—failed to reach the agent. ${message}`,
                }
              : msg,
          ),
        );
      }
    } finally {
      setIsSending(false);
    }
  };

  const backgroundGrid = useMemo(
    () =>
      "linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 40%, var(--gradient-end) 100%)",
    [],
  );

  return (
    <main
      className="relative min-h-screen w-full px-4 py-10 sm:px-10"
      style={{
        background: backgroundGrid,
        color: "var(--text-primary)",
      }}
    >
      {/* Logo in top-left */}
      <div className="absolute left-4 top-4 sm:left-10 sm:top-10">
        <Logo variant="large" />
      </div>
      <ThemeToggle />
      {!isActiveSession ? (
        <WelcomeScreen
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSubmit={() => handleSend()}
          selectedCompanyId={selectedCompanyId}
          onCompanyChange={setSelectedCompanyId}
          startYear={startYear}
          endYear={endYear}
          onStartYearChange={setStartYear}
          onEndYearChange={setEndYear}
        />
      ) : (
        <ActiveShell
          messages={messages}
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSubmit={handleSend}
          chatScrollRef={chatScrollRef}
          ticker={ticker}
          startDate={startDate}
          endDate={endDate}
          moatAssessment={moatAssessment}
          selectedCompanyId={selectedCompanyId}
          onCompanyChange={setSelectedCompanyId}
          startYear={startYear}
          endYear={endYear}
          onStartYearChange={setStartYear}
          onEndYearChange={setEndYear}
        />
      )}
    </main>
  );
}