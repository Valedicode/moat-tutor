"use client";

type EmptyStateProps = {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
};

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="text-center max-w-xs">
        {icon && (
          <div className="mb-4 flex justify-center" style={{ color: "var(--text-tertiary)" }}>
            {icon}
          </div>
        )}
        <h3
          className="text-sm font-semibold mb-2"
          style={{ color: "var(--text-primary)" }}
        >
          {title}
        </h3>
        {description && (
          <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
            {description}
          </p>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className="px-4 py-2 rounded-lg text-xs font-semibold transition-all hover:opacity-80"
            style={{
              backgroundColor: "var(--accent)",
              color: "white",
            }}
          >
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
}
