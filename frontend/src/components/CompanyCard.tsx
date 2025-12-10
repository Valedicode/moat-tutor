"use client";

import { Company } from "@/types/company";

type CompanyCardProps = {
  company: Company;
  isSelected: boolean;
  onToggle: () => void;
};

export function CompanyCard({ company, isSelected, onToggle }: CompanyCardProps) {
  return (
    <button
      onClick={onToggle}
      className="flex flex-col items-center gap-3 rounded-[28px] border-2 p-6 transition-all duration-300 hover:scale-[1.02]"
      style={{
        borderColor: isSelected ? "var(--accent)" : "transparent",
        backgroundColor: isSelected
          ? "color-mix(in srgb, var(--accent) 5%, transparent)"
          : "color-mix(in srgb, var(--surface) 75%, transparent)",
        boxShadow: isSelected 
          ? "none" 
          : "0 0 0 1px var(--border)",
      }}
    >
      {/* Company Logo/Icon */}
      <div
        className="flex h-16 w-16 items-center justify-center rounded-2xl"
        style={{
          backgroundColor: isSelected
            ? "color-mix(in srgb, var(--accent) 15%, transparent)"
            : "var(--surface-secondary)",
        }}
      >
        {company.id === "aapl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "var(--text-primary)" }}>
            <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
          </svg>
        )}
        {company.id === "nvda" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#76b900" }}>
            <path d="M3.5 3v18h17V3h-17zm3.5 4.5h10v1.5H7v-1.5zm0 3h10v1.5H7v-1.5zm0 3h10V15H7v-1.5z"/>
          </svg>
        )}
        {company.id === "msft" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="8" height="8" fill={isSelected ? "var(--accent)" : "#F25022"} />
            <rect x="13" y="3" width="8" height="8" fill={isSelected ? "var(--accent)" : "#7FBA00"} />
            <rect x="3" y="13" width="8" height="8" fill={isSelected ? "var(--accent)" : "#00A4EF"} />
            <rect x="13" y="13" width="8" height="8" fill={isSelected ? "var(--accent)" : "#FFB900"} />
          </svg>
        )}
        {company.id === "googl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "var(--text-primary)" }}>
            <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
          </svg>
        )}
      </div>

      {/* Company Info */}
      <div className="text-center">
        <h3
          className="text-base font-semibold"
          style={{ color: "var(--text-primary)" }}
        >
          {company.name}
        </h3>
        <p
          className="mt-1 text-xs uppercase tracking-wider"
          style={{ color: "var(--text-secondary)" }}
        >
          Sektor: {company.sector}
        </p>
        <p
          className="mt-0.5 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
          Marktcap.: {company.marketCap}
        </p>
      </div>
    </button>
  );
}

