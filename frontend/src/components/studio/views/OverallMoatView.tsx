"use client";

import { useState, useEffect } from "react";
import { getOverallMoatScore, type OverallMoatScore } from "@/lib/moatTutorApi";
import { MoatRadar, type MoatScores } from "@/components/charts";

/** Fixed analysis period for overall moat rating (not user-selected). */
const MOAT_ANALYSIS_START = "2000-01-01";
const MOAT_ANALYSIS_END = "2025-12-31";

type OverallMoatViewProps = {
  ticker?: string | null;
  /** Not used for API; kept for prop compatibility. Moat rating is always 2000-2025. */
  startDate?: string | null;
  /** Not used for API; kept for prop compatibility. Moat rating is always 2000-2025. */
  endDate?: string | null;
  /** Not used; moat rating always uses full range 2000-2025. */
  useFullRange?: boolean;
  /** Whether the card is currently expanded (triggers data loading) */
  isExpanded?: boolean;
};

export function OverallMoatView({
  ticker,
  isExpanded = false,
}: OverallMoatViewProps) {
  const [moatScore, setMoatScore] = useState<OverallMoatScore | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  useEffect(() => {
    const loadMoatScore = async () => {
      // Only load when expanded and not already loaded
      if (!ticker || !isExpanded || hasLoaded) {
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Always request full 2000-2025 range; moat rating is defined for this period only.
        // Note: This is a long-running analysis (can take 30-60 seconds)
        const data = await getOverallMoatScore({
          ticker,
          startDate: MOAT_ANALYSIS_START,
          endDate: MOAT_ANALYSIS_END,
        });
        setMoatScore(data);
        setHasLoaded(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load moat score");
        console.error("Overall moat score error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadMoatScore();
  }, [ticker, isExpanded, hasLoaded]);

  if (!isExpanded && !hasLoaded) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Click to load comprehensive moat analysis
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <div
            className="mb-3 inline-block h-10 w-10 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"
            style={{ color: "var(--accent)" }}
          />
          <p className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
            Loading Full Analysis
          </p>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Analyzing 20+ years of data (this may take 30-60 seconds)...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-sm font-semibold mb-2" style={{ color: "var(--risk)" }}>
            Error loading moat score
          </p>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (!moatScore) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No moat score available
        </p>
      </div>
    );
  }

  const moatScores: MoatScores = {
    networkEffects: moatScore.factors.network_effects,
    switchingCosts: moatScore.factors.switching_costs,
    intangibleAssets: moatScore.factors.intangible_assets,
    costAdvantages: moatScore.factors.cost_advantages,
    efficientScale: moatScore.factors.efficient_scale,
  };

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div
        className="rounded-lg border p-4"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--border-subtle)",
        }}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <span
              className="text-xs uppercase tracking-wider"
              style={{ color: "var(--text-tertiary)" }}
            >
              Overall Moat Rating
            </span>
            <p
              className="text-2xl font-bold mt-1"
              style={{
                color:
                  moatScore.rating === "Wide"
                    ? "#10b981"
                    : moatScore.rating === "Narrow"
                    ? "#eab308"
                    : "#ef4444",
              }}
            >
              {moatScore.rating} Moat
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              Score: {moatScore.overall_score.toFixed(2)} / 5.0
            </p>
          </div>
          <div className="text-right">
            <span
              className="text-xs uppercase tracking-wider"
              style={{ color: "var(--text-tertiary)" }}
            >
              Trend
            </span>
            <p
              className="text-sm font-semibold mt-1"
              style={{
                color:
                  moatScore.trend === "strengthening"
                    ? "#10b981"
                    : moatScore.trend === "weakening"
                    ? "#ef4444"
                    : "var(--text-secondary)",
              }}
            >
              {moatScore.trend === "strengthening" && "↗ Strengthening"}
              {moatScore.trend === "stable" && "→ Stable"}
              {moatScore.trend === "weakening" && "↘ Weakening"}
            </p>
          </div>
        </div>

        <div className="pt-3 border-t" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: "var(--text-tertiary)" }}>
              Analysis Period: {moatScore.time_range}
            </span>
            <span style={{ color: "var(--text-tertiary)" }}>
              Confidence: {moatScore.confidence}
            </span>
          </div>
        </div>
      </div>

      {/* Radar Chart */}
      <div
        className="rounded-lg border p-4"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--background)",
        }}
      >
        <h4
          className="text-xs uppercase tracking-wider font-semibold mb-4"
          style={{ color: "var(--text-secondary)" }}
        >
          Moat Factor Breakdown
        </h4>
        <div className="flex justify-center">
          <MoatRadar scores={moatScores} size={300} />
        </div>
      </div>

      {/* Summary */}
      <div
        className="rounded-lg border p-4"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--surface)",
        }}
      >
        <h4
          className="text-xs uppercase tracking-wider font-semibold mb-2"
          style={{ color: "var(--text-secondary)" }}
        >
          Summary
        </h4>
        <p
          className="text-sm leading-relaxed"
          style={{ color: "var(--text-primary)" }}
        >
          {moatScore.summary}
        </p>
      </div>

      {/* Performance Optimization Note */}
      {(
        <div
          className="rounded-lg border p-3 text-xs"
          style={{
            borderColor: "color-mix(in srgb, var(--accent) 30%, transparent)",
            backgroundColor: "color-mix(in srgb, var(--accent) 5%, transparent)",
            color: "var(--text-secondary)",
          }}
        >
          <div className="flex items-start gap-2">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="flex-shrink-0 mt-0.5"
              style={{ color: "var(--accent)" }}
            >
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            <p>
              <strong style={{ color: "var(--accent)" }}>Optimized:</strong> Using
              cached full-range analysis for maximum performance.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
