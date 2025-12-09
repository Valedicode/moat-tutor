"use client";

type ExamplePromptsProps = {
  onSelect: (prompt: string) => void;
};

const examplePrompts = [
  "Explain moat evolution",
  "News-to-price correlation",
  "Key events summary",
];

export function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="flex flex-col gap-3 items-center">
      <p
        className="text-xs uppercase tracking-wider"
        style={{ color: "var(--text-tertiary)" }}
      >
        Example Prompts
      </p>
      <div className="flex flex-wrap gap-2 justify-center">
        {examplePrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelect(prompt)}
            className="rounded-full border px-4 py-2 text-sm transition-all hover:scale-105"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "color-mix(in srgb, var(--surface) 75%, transparent)",
              color: "var(--text-primary)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--accent)";
              e.currentTarget.style.backgroundColor = "color-mix(in srgb, var(--accent) 10%, transparent)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.backgroundColor = "color-mix(in srgb, var(--surface) 75%, transparent)";
            }}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}

