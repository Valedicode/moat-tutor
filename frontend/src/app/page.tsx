"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Message } from "@/types/chat";
import { IdleHero } from "@/components/IdleHero";
import { ActiveShell } from "@/components/ActiveShell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { assistantNarratives } from "@/constants/chat";
import { nowStamp } from "@/utils/date";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isListening, setIsListening] = useState(false);
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

  const handleSend = (value?: string) => {
    const text = (value ?? inputValue).trim();
    if (!text) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: nowStamp(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");

    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content:
        assistantNarratives[
          Math.floor(Math.random() * assistantNarratives.length)
        ],
      timestamp: nowStamp(),
    };

    setTimeout(() => {
      setMessages((prev) => [...prev, assistantMessage]);
    }, 700);
  };

  const backgroundGrid = useMemo(
    () =>
      "linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-mid) 40%, var(--gradient-end) 100%)",
    [],
  );

  return (
    <main
      className="min-h-screen w-full px-4 py-10 sm:px-10"
      style={{
        background: backgroundGrid,
        color: "var(--text-primary)",
      }}
    >
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
