"use client";

import { useState, useEffect } from "react";

type DateRangePickerProps = {
  value: number; // Number of years back from 2023
  onChange: (years: number) => void;
};

export function DateRangePicker({ value, onChange }: DateRangePickerProps) {
  const [localValue, setLocalValue] = useState(value);
  const maxYears = 7; // Maximum 7 years back from 2023
  const minYears = 1; // Minimum 1 year

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value);
    setLocalValue(newValue);
    onChange(newValue);
  };

  const getStartYear = () => {
    return 2023 - localValue;
  };

  const getEndYear = () => {
    return 2023;
  };

  const quickSelectOptions = [
    { label: "1J", years: 1 },
    { label: "3J", years: 3 },
    { label: "5J", years: 5 },
    { label: "Max", years: maxYears },
  ];

  return (
    <div className="flex flex-col gap-3">
      <label
        className="text-sm font-medium uppercase tracking-wider"
        style={{ color: "var(--text-primary)" }}
      >
        Date Range Picker
      </label>

      {/* Quick select buttons */}
      <div className="flex gap-2">
        {quickSelectOptions.map((option) => (
          <button
            key={option.label}
            type="button"
            onClick={() => {
              setLocalValue(option.years);
              onChange(option.years);
            }}
            className="rounded-lg border px-3 py-1.5 text-sm transition-all"
            style={{
              borderColor:
                localValue === option.years
                  ? "var(--accent)"
                  : "var(--border)",
              backgroundColor:
                localValue === option.years
                  ? "color-mix(in srgb, var(--accent) 10%, transparent)"
                  : "transparent",
              color:
                localValue === option.years
                  ? "var(--accent)"
                  : "var(--text-secondary)",
            }}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Slider */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span
            className="text-xs"
            style={{ color: "var(--text-tertiary)" }}
          >
            {getStartYear()} - {getEndYear()}
          </span>
          <span
            className="text-xs font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            {localValue} {localValue === 1 ? "Year" : "Years"}
          </span>
        </div>
        <div className="relative">
          <input
            type="range"
            min={minYears}
            max={maxYears}
            value={localValue}
            onChange={handleChange}
            className="range-slider h-2 w-full cursor-pointer appearance-none rounded-lg"
            style={{
              background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${
                ((localValue - minYears) / (maxYears - minYears)) * 100
              }%, var(--border) ${
                ((localValue - minYears) / (maxYears - minYears)) * 100
              }%, var(--border) 100%)`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

