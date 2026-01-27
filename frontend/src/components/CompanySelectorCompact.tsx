"use client";

import { useState, useRef, useEffect } from "react";
import { availableCompanies } from "@/constants/companies";

type CompanySelectorCompactProps = {
  selectedCompanyId: string | null;
  onCompanyChange: (companyId: string | null) => void;
};

export function CompanySelectorCompact({
  selectedCompanyId,
  onCompanyChange,
}: CompanySelectorCompactProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const selectedCompany = selectedCompanyId
    ? availableCompanies.find((c) => c.id === selectedCompanyId)
    : null;

  // Filter companies based on search query
  const filteredCompanies = availableCompanies.filter((company) =>
    company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    company.ticker.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchQuery("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectCompany = (companyId: string) => {
    onCompanyChange(companyId);
    setIsOpen(false);
    setSearchQuery("");
  };

  return (
    <div className="relative w-full">
      {/* Trigger Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full rounded-lg border px-3 py-2 text-left transition-all hover:border-opacity-80"
        style={{
          borderColor: selectedCompany ? "var(--accent)" : "var(--border)",
          backgroundColor: "var(--background)",
          color: "var(--text-primary)",
        }}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 min-w-0">
            {selectedCompany ? (
              <>
                <p className="text-sm font-semibold truncate">{selectedCompany.ticker}</p>
                <p className="text-xs truncate" style={{ color: "var(--text-tertiary)" }}>
                  {selectedCompany.name}
                </p>
              </>
            ) : (
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Select company...
              </p>
            )}
          </div>
          <svg
            className={`flex-shrink-0 h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style={{ color: "var(--text-secondary)" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-50 mt-2 w-full rounded-lg border shadow-lg animate-in fade-in slide-in-from-top-2 duration-200"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "var(--background)",
          }}
        >
          {/* Search Input */}
          <div className="p-2 border-b" style={{ borderColor: "var(--border)" }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search..."
              className="w-full rounded px-2 py-1.5 text-sm border focus:outline-none focus:ring-1"
              style={{
                borderColor: "var(--border)",
                backgroundColor: "var(--surface)",
                color: "var(--text-primary)",
              }}
              autoFocus
            />
          </div>

          {/* Company List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredCompanies.length > 0 ? (
              filteredCompanies.map((company) => (
                <button
                  key={company.id}
                  type="button"
                  onClick={() => handleSelectCompany(company.id)}
                  className="w-full px-3 py-2 text-left transition-colors hover:bg-opacity-50"
                  style={{
                    backgroundColor:
                      selectedCompanyId === company.id
                        ? "color-mix(in srgb, var(--accent) 15%, transparent)"
                        : "transparent",
                    color: "var(--text-primary)",
                  }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">{company.ticker}</p>
                      <p className="text-xs truncate" style={{ color: "var(--text-tertiary)" }}>
                        {company.name}
                      </p>
                    </div>
                    {selectedCompanyId === company.id && (
                      <div
                        className="h-2 w-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: "var(--accent)" }}
                      />
                    )}
                  </div>
                </button>
              ))
            ) : (
              <div className="px-3 py-4 text-center text-xs" style={{ color: "var(--text-secondary)" }}>
                No companies found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
