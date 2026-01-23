"use client";

import { useState } from "react";

type StudioCardProps = {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  available: boolean;
  onClick: () => void;
  isExpanded: boolean;
  isLoading?: boolean;
};

export function StudioCard({
  title,
  description,
  icon,
  available,
  onClick,
  isExpanded,
  isLoading,
}: StudioCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      disabled={!available}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="w-full text-left transition-all duration-200"
      style={{
        opacity: available ? 1 : 0.5,
        cursor: available ? "pointer" : "not-allowed",
      }}
    >
      <div
        className="rounded-xl border p-4 transition-all"
        style={{
          borderColor: isExpanded
            ? "var(--accent)"
            : isHovered && available
            ? "var(--accent)"
            : "var(--border)",
          backgroundColor: isExpanded
            ? "color-mix(in srgb, var(--accent) 10%, transparent)"
            : isHovered && available
            ? "color-mix(in srgb, var(--surface) 50%, transparent)"
            : "var(--background)",
          transform: isHovered && available ? "translateY(-2px)" : "none",
        }}
      >
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div
            className="flex-shrink-0 mt-0.5"
            style={{
              color: isExpanded ? "var(--accent)" : "var(--text-secondary)",
            }}
          >
            {icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4
                className="text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {title}
              </h4>
              {isLoading && (
                <div
                  className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"
                  style={{ color: "var(--accent)" }}
                />
              )}
            </div>
            <p
              className="text-xs leading-relaxed"
              style={{ color: "var(--text-secondary)" }}
            >
              {description}
            </p>
            {!available && (
              <p
                className="text-xs mt-1 italic"
                style={{ color: "var(--text-tertiary)" }}
              >
                Select a company in Sources to enable
              </p>
            )}
          </div>

          {/* Expand indicator */}
          {available && (
            <div
              className="flex-shrink-0"
              style={{ color: "var(--text-tertiary)" }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className={`transition-transform ${isExpanded ? "rotate-180" : ""}`}
              >
                <path d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}
