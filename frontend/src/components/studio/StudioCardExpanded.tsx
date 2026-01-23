"use client";

type StudioCardExpandedProps = {
  children: React.ReactNode;
  onCollapse: () => void;
};

export function StudioCardExpanded({ children, onCollapse }: StudioCardExpandedProps) {
  return (
    <div
      className="rounded-xl border p-4 mb-4 animate-in fade-in slide-in-from-top-2 duration-300"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "var(--background)",
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <h4
          className="text-xs uppercase tracking-wider font-semibold"
          style={{ color: "var(--text-secondary)" }}
        >
          Visualization
        </h4>
        <button
          onClick={onCollapse}
          className="p-1 rounded-lg hover:bg-opacity-20 transition-all"
          style={{ color: "var(--text-secondary)" }}
          title="Collapse"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M18 15l-6-6-6 6" />
          </svg>
        </button>
      </div>
      <div>{children}</div>
    </div>
  );
}
