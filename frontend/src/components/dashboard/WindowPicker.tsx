"use client";

import React, { useState, useEffect } from "react";
import { TimeWindow, getAvailableWindows } from "@/lib/moatTutorApi";

interface WindowPickerProps {
  onWindowSelected: (windowLabel: string, window: TimeWindow) => void;
  selectedWindow?: string;
}

export function WindowPicker({ onWindowSelected, selectedWindow }: WindowPickerProps) {
  const [windows, setWindows] = useState<Record<string, TimeWindow> | null>(null);
  const [loading, setLoading] = useState(true);
  const [customMode, setCustomMode] = useState(false);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  useEffect(() => {
    loadWindows();
  }, []);

  const loadWindows = async () => {
    try {
      const data = await getAvailableWindows();
      setWindows(data);
    } catch (err) {
      console.error("Failed to load windows:", err);
    } finally {
      setLoading(false);
    }
  };

  const getPolicyBadge = (outputMode: string) => {
    switch (outputMode) {
      case "rating":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            Full Rating
          </span>
        );
      case "direction":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
            Direction Only
          </span>
        );
      case "signals":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
            Signals Only
          </span>
        );
      default:
        return null;
    }
  };

  const getWindowIcon = (windowType: string) => {
    switch (windowType) {
      case "structural":
        return "🏛️";
      case "phase":
        return "📊";
      case "signal":
        return "🔔";
      default:
        return "📅";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!windows) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
        Failed to load available windows
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toggle between preset and custom */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Select Time Window</h3>
        <button
          onClick={() => setCustomMode(!customMode)}
          className="text-xs text-blue-600 hover:text-blue-700"
        >
          {customMode ? "Use Preset" : "Custom Range"}
        </button>
      </div>

      {!customMode ? (
        /* Preset Windows */
        <div className="grid grid-cols-1 gap-2">
          {Object.entries(windows).map(([label, window]) => (
            <button
              key={label}
              onClick={() => onWindowSelected(label, window)}
              className={`
                p-3 border rounded-lg text-left transition-all
                ${
                  selectedWindow === label
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300 bg-white"
                }
              `}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getWindowIcon(window.window_type)}</span>
                    <span className="font-medium text-gray-900">{window.description}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {window.start_date} to {window.end_date} ({window.duration_years.toFixed(1)}y)
                  </div>
                </div>
                <div>{getPolicyBadge(window.policy.output_mode)}</div>
              </div>

              {/* Policy details */}
              {window.policy.require_disclaimer && (
                <div className="mt-2 text-xs text-yellow-700 bg-yellow-50 px-2 py-1 rounded">
                  ⚠️ Requires uncertainty disclaimer
                </div>
              )}
            </button>
          ))}
        </div>
      ) : (
        /* Custom Window Form */
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          <button
            onClick={() => {
              if (customStart && customEnd) {
                // Calculate duration
                const start = new Date(customStart);
                const end = new Date(customEnd);
                const durationYears = (end.getTime() - start.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
                
                // Determine policy based on duration
                let outputMode: "rating" | "direction" | "signals" = "signals";
                if (durationYears >= 8) outputMode = "rating";
                else if (durationYears >= 3) outputMode = "direction";

                const customWindow: TimeWindow = {
                  label: "custom",
                  window_type: durationYears >= 8 ? "structural" : durationYears >= 3 ? "phase" : "signal",
                  start_date: customStart,
                  end_date: customEnd,
                  duration_years: durationYears,
                  description: `Custom window (${durationYears.toFixed(1)} years)`,
                  policy: {
                    output_mode: outputMode,
                    allow_rating: outputMode === "rating",
                    allow_scores: outputMode !== "signals",
                    require_disclaimer: outputMode !== "rating",
                  },
                };
                
                onWindowSelected("custom", customWindow);
              }
            }}
            disabled={!customStart || !customEnd}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
          >
            Apply Custom Window
          </button>

          {customStart && customEnd && (
            <div className="text-xs text-gray-600">
              <div>Duration: {((new Date(customEnd).getTime() - new Date(customStart).getTime()) / (365.25 * 24 * 60 * 60 * 1000)).toFixed(1)} years</div>
              <div className="mt-1">
                Policy: {
                  ((new Date(customEnd).getTime() - new Date(customStart).getTime()) / (365.25 * 24 * 60 * 60 * 1000)) >= 8
                    ? "Full rating allowed"
                    : ((new Date(customEnd).getTime() - new Date(customStart).getTime()) / (365.25 * 24 * 60 * 60 * 1000)) >= 3
                    ? "Direction only"
                    : "Signals only"
                }
              </div>
            </div>
          )}
        </div>
      )}

      {/* Policy Legend */}
      <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Policy Guide</h4>
        <div className="space-y-1 text-xs text-gray-600">
          <div className="flex items-center gap-2">
            {getPolicyBadge("rating")}
            <span>≥8 years: Full structural rating (Wide/Narrow/None)</span>
          </div>
          <div className="flex items-center gap-2">
            {getPolicyBadge("direction")}
            <span>3-7 years: Direction only (Strengthening/Stable/Weakening)</span>
          </div>
          <div className="flex items-center gap-2">
            {getPolicyBadge("signals")}
            <span>&lt;3 years: Tactical signals only (no moat assessment)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
