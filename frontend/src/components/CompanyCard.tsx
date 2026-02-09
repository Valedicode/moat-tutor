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
        {company.id === "avgo" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#e53935" }}>
            <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5zm0 10h7c-.53 4.12-3.28 7.79-7 8.94V12H5V7.89l7-3.78v7.89z"/>
          </svg>
        )}
        {company.id === "orcl" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#f80000" }}>
            <path d="M17.5 4h-11C4.5 4 3 5.5 3 7.5v9C3 18.5 4.5 20 6.5 20h11c2 0 3.5-1.5 3.5-3.5v-9C21 5.5 19.5 4 17.5 4zm1 12.5c0 .83-.67 1.5-1.5 1.5h-11c-.83 0-1.5-.67-1.5-1.5v-9c0-.83.67-1.5 1.5-1.5h11c.83 0 1.5.67 1.5 1.5v9z"/>
            <path d="M7 12c0-2.76 2.24-5 5-5s5 2.24 5 5-2.24 5-5 5-5-2.24-5-5zm2 0c0 1.66 1.34 3 3 3s3-1.34 3-3-1.34-3-3-3-3 1.34-3 3z"/>
          </svg>
        )}
        {company.id === "amd" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#ed1c24" }}>
            <path d="M3 3l6 18h3L18 3h-3l-4.5 13.5L6 3H3zm15 0l3 9v9h-6l-3-9h3l1.5 4.5L18 9h-3l3-6z"/>
          </svg>
        )}
        {company.id === "csco" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#049fd9" }}>
            <path d="M3 14h2v7H3v-7zm4-4h2v11H7V10zm4-7h2v18h-2V3zm4 4h2v14h-2V7zm4 3h2v11h-2V10z"/>
          </svg>
        )}
        {company.id === "pltr" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "var(--text-primary)" }}>
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18l7.6 3.8L12 11.78l-7.6-3.8L12 4.18zM4 9.19l7 3.5v7.12l-7-3.5V9.19zm16 0v7.12l-7 3.5v-7.12l7-3.5z"/>
          </svg>
        )}
        {company.id === "mu" && (
          <svg className="h-10 w-10" viewBox="0 0 24 24" fill="currentColor" style={{ color: isSelected ? "var(--accent)" : "#0079c1" }}>
            <path d="M3 3v18h18V3H3zm16 16H5V5h14v14z"/>
            <path d="M7 7v10h2V9.5L11 14l2-4.5V17h2V7h-2l-2 5-2-5H7z"/>
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
          Sector: {company.sector}
        </p>
        <p
          className="mt-0.5 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
          Marktcap.: {company.marketCap}
        </p>
        {/* Historical Data Indicator */}
        {company.historicalNewsAvailable && (
          <div
            className="mt-2 inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium"
            style={{
              backgroundColor: "color-mix(in srgb, var(--accent) 10%, transparent)",
              color: "var(--accent)",
            }}
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Historical Data (2000-2023)
          </div>
        )}
      </div>
    </button>
  );
}

