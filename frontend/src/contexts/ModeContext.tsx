"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type ChatMode = "analyst" | "tutor";

type ModeContextType = {
  mode: ChatMode;
  setMode: (mode: ChatMode) => void;
  toggleMode: () => void;
};

const ModeContext = createContext<ModeContextType | undefined>(undefined);

export function ModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ChatMode>("analyst");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("chatMode") as ChatMode | null;
    if (saved === "analyst" || saved === "tutor") {
      setModeState(saved);
    }
  }, []);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem("chatMode", mode);
  }, [mode, mounted]);

  const setMode = (next: ChatMode) => setModeState(next);
  const toggleMode = () =>
    setModeState((prev) => (prev === "analyst" ? "tutor" : "analyst"));

  if (!mounted) {
    return null;
  }

  return (
    <ModeContext.Provider value={{ mode, setMode, toggleMode }}>
      {children}
    </ModeContext.Provider>
  );
}

export function useMode() {
  const context = useContext(ModeContext);
  if (context === undefined) {
    throw new Error("useMode must be used within a ModeProvider");
  }
  return context;
}
