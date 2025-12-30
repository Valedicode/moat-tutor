"use client";

import { ChatInput } from "@/components/chat";
import { CompanyCard } from "@/components/CompanyCard";
import { DateRangePicker } from "@/components/DateRangePicker";
import { ExamplePrompts } from "@/components/ExamplePrompts";
import { availableCompanies } from "@/constants/companies";

type WelcomeScreenProps = {
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  selectedCompanyId: string | null;
  onCompanyChange: (companyId: string | null) => void;
  dateRangeYears: number;
  onDateRangeChange: (years: number) => void;
};

export function WelcomeScreen({
  inputValue,
  onInputChange,
  onSubmit,
  selectedCompanyId,
  onCompanyChange,
  dateRangeYears,
  onDateRangeChange,
}: WelcomeScreenProps) {
  const toggleCompany = (companyId: string) => {
    onCompanyChange(selectedCompanyId === companyId ? null : companyId);
  };

  return (
    <section className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-5xl flex-col items-center justify-center text-center">
      <p
        className="text-base uppercase tracking-[0.35em]"
        style={{ color: "var(--text-secondary)" }}
      >
        Moat Tutor
      </p>
      <h1
        className="mt-5 text-3xl font-semibold leading-tight md:text-4xl"
        style={{ color: "var(--text-primary)" }}
      >
        Which company do you want to explore?
      </h1>
      <p
        className="mt-3 max-w-2xl text-balance text-base"
        style={{ color: "var(--text-secondary)" }}
      >
        Select a company and analyze its Moat development.
      </p>

      <div className="mt-6 w-full max-w-2xl mx-auto">
        <ExamplePrompts
          onSelect={(prompt) => {
            onInputChange(prompt);
          }}
        />
      </div>

      {/* Chat Input */}
      <div className="mt-1 w-full max-w-2xl">
        <ChatInput
          value={inputValue}
          onChange={onInputChange}
          onSubmit={onSubmit}
          variant="idle"
          placeholder="Ask any question"
        />
      </div>	

      {/* Company Selection Grid */}
      <div className="mt-10 grid w-full grid-cols-2 gap-4 md:grid-cols-4 md:gap-6">
        {availableCompanies.map((company) => (
          <CompanyCard
            key={company.id}
            company={company}
            isSelected={selectedCompanyId === company.id}
            onToggle={() => toggleCompany(company.id)}
          />
        ))}
      </div>

      {/* Date Range Picker */}
      <div className="mt-8 w-full max-w-md">
        <DateRangePicker value={dateRangeYears} onChange={onDateRangeChange} />
      </div>
    </section>
  );
}

