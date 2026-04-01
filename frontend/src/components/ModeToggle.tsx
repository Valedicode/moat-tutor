"use client";

import { useMode, type ChatMode } from "@/contexts/ModeContext";

const OPTIONS: { value: ChatMode; label: string }[] = [
  { value: "analyst", label: "Analyst" },
  { value: "tutor", label: "Tutor" },
];

type ModeToggleProps = {
  disabled?: boolean;
};

export function ModeToggle({ disabled = false }: ModeToggleProps) {
  const { mode, setMode } = useMode();

  return (
    <div
      className="flex rounded-full p-0.5"
      style={{
        backgroundColor: "color-mix(in srgb, var(--text-secondary) 12%, transparent)",
        opacity: disabled ? 0.45 : 1,
        cursor: disabled ? "not-allowed" : "default",
      }}
      title={disabled ? "Mode is locked while generating" : undefined}
    >
      {OPTIONS.map((opt) => {
        const active = mode === opt.value;
        return (
          <button
            key={opt.value}
            disabled={disabled}
            onClick={() => setMode(opt.value)}
            className="relative rounded-full px-3 py-1 text-xs font-medium transition-colors duration-200"
            style={{
              backgroundColor: active ? "var(--accent)" : "transparent",
              color: active ? "#fff" : "var(--text-secondary)",
              pointerEvents: disabled ? "none" : "auto",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
