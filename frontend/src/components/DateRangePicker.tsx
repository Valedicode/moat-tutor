"use client";

import { useState, useEffect } from "react";

type DateRangePickerProps = {
  startYear: number; // Start year (2000-2025)
  endYear: number; // End year (2000-2025)
  onStartYearChange: (year: number) => void;
  onEndYearChange: (year: number) => void;
};

const MIN_YEAR = 2000;
const MAX_YEAR = 2025;

export function DateRangePicker({
  startYear,
  endYear,
  onStartYearChange,
  onEndYearChange,
}: DateRangePickerProps) {
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
    // Ensure start <= end
    if (newStart <= localEndYear) {
      setLocalStartYear(newStart);
      onStartYearChange(newStart);
    }
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnd = parseInt(e.target.value);
    // Ensure end >= start
    if (newEnd >= localStartYear) {
      setLocalEndYear(newEnd);
      onEndYearChange(newEnd);
    }
  };

  const getStartDate = () => `${localStartYear}-01-01`;
  const getEndDate = () => `${localEndYear}-12-31`;

  // Calculate percentage positions for visual indicators
  // Account for thumb width (10px padding on each side = 20px total)
  const totalYears = MAX_YEAR - MIN_YEAR;
  const startPercent = ((localStartYear - MIN_YEAR) / totalYears) * 100;
  const endPercent = ((localEndYear - MIN_YEAR) / totalYears) * 100;
  
  // Calculate the actual fill width percentage
  const fillWidthPercent = endPercent - startPercent;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label
          className="text-base font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-primary)" }}
        >
          Date Range Selection
        </label>
        <p
          className="text-sm"
          style={{ color: "#595959" }}
        >
          Select start and end year (2000-2025)
        </p>
      </div>

      {/* Dual Range Slider */}
      <div className="flex flex-col gap-4">
        {/* Year Display */}
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span
              className="text-sm font-semibold"
              style={{ color: "#333333" }}
            >
              {getStartDate()}
            </span>
            <span
              className="text-xs mt-0.5"
              style={{ color: "#808080" }}
            >
              Start date
            </span>
          </div>
          <div className="flex flex-col items-center">
            <span
              className="text-sm font-medium"
              style={{ color: "#595959" }}
            >
              {localEndYear - localStartYear} {localEndYear - localStartYear === 1 ? "year" : "years"}
            </span>
            <span
              className="text-xs mt-0.5"
              style={{ color: "#808080" }}
            >
              Duration
            </span>
          </div>
          <div className="flex flex-col items-end">
            <span
              className="text-sm font-semibold"
              style={{ color: "#333333" }}
            >
              {getEndDate()}
            </span>
            <span
              className="text-xs mt-0.5"
              style={{ color: "#808080" }}
            >
              End date
            </span>
          </div>
        </div>

        {/* Dual Range Slider Container */}
        <div className="relative" style={{ height: "40px", paddingTop: "15px", paddingBottom: "15px", paddingLeft: "10px", paddingRight: "10px" }}>
          {/* Track Background */}
          <div
            className="absolute top-1/2 h-2.5 -translate-y-1/2 rounded-lg"
            style={{ 
              backgroundColor: "var(--border)", 
              zIndex: 1,
              left: "10px",
              right: "10px",
              width: "calc(100% - 20px)",
            }}
          />

          {/* Selected Range Fill */}
          <div
            className="absolute top-1/2 h-2.5 -translate-y-1/2 rounded-lg transition-all duration-150"
            style={{
              left: `calc(10px + (100% - 20px) * ${startPercent} / 100)`,
              width: `calc((100% - 20px) * ${fillWidthPercent} / 100)`,
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
            aria-label={`Select start year: ${localStartYear}`}
            aria-valuemin={MIN_YEAR}
            aria-valuemax={localEndYear}
            aria-valuenow={localStartYear}
            className="range-slider-dual absolute top-1/2 -translate-y-1/2 cursor-pointer"
            style={{
              zIndex: localStartYear === localEndYear ? 4 : 3,
              height: "20px",
              margin: 0,
              padding: 0,
              left: "10px",
              right: "10px",
              width: "calc(100% - 20px)",
            }}
          />

          {/* End Year Slider */}
          <input
            type="range"
            min={MIN_YEAR}
            max={MAX_YEAR}
            value={localEndYear}
            onChange={handleEndChange}
            aria-label={`Select end year: ${localEndYear}`}
            aria-valuemin={localStartYear}
            aria-valuemax={MAX_YEAR}
            aria-valuenow={localEndYear}
            className="range-slider-dual absolute top-1/2 -translate-y-1/2 cursor-pointer"
            style={{
              zIndex: 4,
              height: "20px",
              margin: 0,
              padding: 0,
              left: "10px",
              right: "10px",
              width: "calc(100% - 20px)",
            }}
          />
        </div>

        {/* Year Labels Below Slider - Show milestone years (every 5 years) + selected years */}
        <div className="flex justify-between text-xs" style={{ color: "#808080", paddingLeft: "10px", paddingRight: "10px" }}>
          {(() => {
            // Create milestone years (every 5 years)
            const milestoneYears = [];
            for (let year = MIN_YEAR; year <= MAX_YEAR; year += 5) {
              milestoneYears.push(year);
            }
            // Add MAX_YEAR if it's not already included
            if (!milestoneYears.includes(MAX_YEAR)) {
              milestoneYears.push(MAX_YEAR);
            }
            // Add selected years if they're not milestones
            if (!milestoneYears.includes(localStartYear)) {
              milestoneYears.push(localStartYear);
            }
            if (!milestoneYears.includes(localEndYear)) {
              milestoneYears.push(localEndYear);
            }
            // Sort and deduplicate
            const displayYears = [...new Set(milestoneYears)].sort((a, b) => a - b);
            
            return displayYears.map((year) => (
              <button
                key={year}
                type="button"
                onClick={() => {
                  // If clicking closer to start, set start; otherwise set end
                  const startDistance = Math.abs(year - localStartYear);
                  const endDistance = Math.abs(year - localEndYear);
                  if (startDistance <= endDistance && year <= localEndYear) {
                    setLocalStartYear(year);
                    onStartYearChange(year);
                  } else if (year >= localStartYear) {
                    setLocalEndYear(year);
                    onEndYearChange(year);
                  }
                }}
                className="transition-opacity hover:opacity-70 hover:underline"
                style={{
                  fontWeight: year === localStartYear || year === localEndYear ? 600 : 400,
                  color:
                    year >= localStartYear && year <= localEndYear
                      ? "var(--accent)"
                      : "#808080",
                }}
                aria-label={`Set year to ${year}`}
              >
                {year}
              </button>
            ));
          })()}
        </div>

        <p
          className="text-xs text-center"
          style={{ color: "#808080" }}
        >
          Drag handles or click year labels to adjust range
        </p>
      </div>
    </div>
  );
}

