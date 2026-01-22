"use client";

import { ChatInput } from "@/components/chat";
import { CompanySelector } from "@/components/CompanySelector";
import { DateRangePicker } from "@/components/DateRangePicker";
import { ExamplePrompts } from "@/components/ExamplePrompts";

type WelcomeScreenProps = {
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  selectedCompanyId: string | null;
  onCompanyChange: (companyId: string | null) => void;
  startYear: number;
  endYear: number;
  onStartYearChange: (year: number) => void;
  onEndYearChange: (year: number) => void;
};

export function WelcomeScreen({
  inputValue,
  onInputChange,
  onSubmit,
  selectedCompanyId,
  onCompanyChange,
  startYear,
  endYear,
  onStartYearChange,
  onEndYearChange,
}: WelcomeScreenProps) {
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

      {/* Company Selector - Searchable Dropdown with Card Preview */}
      <div className="mt-8 w-full">
        <CompanySelector
          selectedCompanyId={selectedCompanyId}
          onCompanyChange={onCompanyChange}
        />
      </div>

      {/* Date Range Picker */}
      <div className="mt-8 w-full max-w-md">
        <DateRangePicker
          startYear={startYear}
          endYear={endYear}
          onStartYearChange={onStartYearChange}
          onEndYearChange={onEndYearChange}
        />
      </div>
    </section>
  );
}

