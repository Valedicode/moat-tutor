"use client";

import { useState, useEffect } from "react";

type DateRangePickerCompactProps = {
  startYear: number;
  endYear: number;
  onStartYearChange: (year: number) => void;
  onEndYearChange: (year: number) => void;
};

const MIN_YEAR = 2000;
const MAX_YEAR = 2025;

export function DateRangePickerCompact({
  startYear,
  endYear,
  onStartYearChange,
  onEndYearChange,
}: DateRangePickerCompactProps) {
  const [localStartYear, setLocalStartYear] = useState(startYear);
  const [localEndYear, setLocalEndYear] = useState(endYear);

  useEffect(() => {
    setLocalStartYear(startYear);
  }, [startYear]);

  useEffect(() => {
    setLocalEndYear(endYear);
  }, [endYear]);

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newStart = parseInt(e.target.value);
    if (newStart <= localEndYear) {
      setLocalStartYear(newStart);
      onStartYearChange(newStart);
    }
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnd = parseInt(e.target.value);
    if (newEnd >= localStartYear) {
      setLocalEndYear(newEnd);
      onEndYearChange(newEnd);
    }
  };

  const totalYears = MAX_YEAR - MIN_YEAR;
  const startPercent = ((localStartYear - MIN_YEAR) / totalYears) * 100;
  const endPercent = ((localEndYear - MIN_YEAR) / totalYears) * 100;
  const fillWidthPercent = endPercent - startPercent;

  return (
    <div className="flex flex-col gap-3">
      {/* Year Display */}
      <div className="flex items-center justify-between text-xs">
        <div>
          <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
            {localStartYear}
          </span>
          <span className="ml-1" style={{ color: "var(--text-tertiary)" }}>
            Start
          </span>
        </div>
        <div>
          <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
            {localEndYear}
          </span>
          <span className="ml-1" style={{ color: "var(--text-tertiary)" }}>
            End
          </span>
        </div>
      </div>

      {/* Dual Range Slider */}
      <div className="relative" style={{ height: "32px", paddingTop: "12px", paddingBottom: "12px" }}>
        {/* Track Background */}
        <div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full"
          style={{
            backgroundColor: "var(--border)",
            zIndex: 1,
            left: 0,
            right: 0,
          }}
        />

        {/* Selected Range Fill */}
        <div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full transition-all duration-150"
          style={{
            left: `${startPercent}%`,
            width: `${fillWidthPercent}%`,
            backgroundColor: "var(--accent)",
            zIndex: 2,
          }}
        />

        {/* Start Year Slider */}
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={localStartYear}
          onChange={handleStartChange}
          className="range-slider-dual absolute top-1/2 -translate-y-1/2 cursor-pointer"
          style={{
            zIndex: 3,
            height: "16px",
            width: "100%",
          }}
        />

        {/* End Year Slider */}
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={localEndYear}
          onChange={handleEndChange}
          className="range-slider-dual absolute top-1/2 -translate-y-1/2 cursor-pointer"
          style={{
            zIndex: 4,
            height: "16px",
            width: "100%",
          }}
        />
      </div>

      {/* Year Labels */}
      <div className="flex justify-between text-xs" style={{ color: "var(--text-tertiary)" }}>
        <span>{MIN_YEAR}</span>
        <span>{Math.floor((MIN_YEAR + MAX_YEAR) / 2)}</span>
        <span>{MAX_YEAR}</span>
      </div>
    </div>
  );
}
