"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Message } from "@/types/chat";
import { IdleHero } from "@/components/IdleHero";
import { ActiveShell } from "@/components/ActiveShell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Logo } from "@/components/Logo";
import { nowStamp } from "@/utils/date";
import { chat, chatStream, type StreamEvent } from "@/lib/moatTutorApi";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [visualizerLevels, setVisualizerLevels] = useState<number[]>(
    () => Array.from({ length: 16 }, () => 10),
  );
  const streamRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  const isActiveSession = messages.length > 0;

  useEffect(() => {
    if (!isListening) {
      if (streamRef.current) {
        clearInterval(streamRef.current);
        streamRef.current = null;
      }
      return;
    }

    streamRef.current = setInterval(() => {
      setVisualizerLevels((levels) =>
        levels.map(() => 6 + Math.random() * 38),
      );
    }, 150);

    return () => {
      if (streamRef.current) {
        clearInterval(streamRef.current);
        streamRef.current = null;
      }
    };
  }, [isListening]);

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
          } else if (evt.event === "error") {
            throw new Error(evt.data.error);
          }
        },
      });
    } catch (error) {
      try {
        const result = await chat({ query: text, sessionId });
        setSessionId(result.session_id);
        setMessages((prev) =>
          prev.map((msg) => (msg.id === placeholderId ? result.message : msg)),
        );
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
        <IdleHero
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSubmit={() => handleSend()}
          toggleListening={() => setIsListening((prev) => !prev)}
        />
      ) : (
        <ActiveShell
          messages={messages}
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSubmit={handleSend}
          chatScrollRef={chatScrollRef}
          toggleListening={() => setIsListening((prev) => !prev)}
        />
      )}
    </main>
  );
}