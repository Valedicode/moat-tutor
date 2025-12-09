"use client";

type LogoProps = {
  variant?: "large" | "small";
  className?: string;
};

export function Logo({ variant = "large", className = "" }: LogoProps) {
  const textSize = variant === "large" ? "text-2xl font-bold" : "text-lg font-semibold";
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span
        className={textSize}
        style={{ color: "var(--text-primary)" }}
      >
        MOAT
      </span>
      <span
        className={textSize}
        style={{ color: "var(--accent)" }}
      >
        TUTOR
      </span>
    </div>
  );
}

