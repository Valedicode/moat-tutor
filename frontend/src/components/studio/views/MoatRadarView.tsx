"use client";

import { MoatRadar, type MoatScores } from "@/components/charts";
import { type MoatAssessment } from "@/lib/moatTutorApi";

type MoatRadarViewProps = {
  moatAssessment?: MoatAssessment | null;
};

export function MoatRadarView({ moatAssessment }: MoatRadarViewProps) {
  if (!moatAssessment) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No moat assessment available. Ask a question in chat to generate an analysis.
        </p>
      </div>
    );
  }

  const moatScores: MoatScores = {
    networkEffects: moatAssessment.network_effects.score,
    switchingCosts: moatAssessment.switching_costs.score,
    intangibleAssets: moatAssessment.intangible_assets.score,
    costAdvantages: moatAssessment.cost_advantages.score,
    efficientScale: moatAssessment.efficient_scale.score,
  };

  return (
    <div className="space-y-4">
      {/* Moat Rating Badge */}
      <div
        className="rounded-lg border p-3"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--border-subtle)",
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <span
              className="text-xs uppercase tracking-wider"
              style={{ color: "var(--text-tertiary)" }}
            >
              Rating
            </span>
            <p
              className="text-lg font-bold mt-1"
              style={{
                color:
                  moatAssessment.overall_rating === "Wide"
                    ? "#10b981"
                    : moatAssessment.overall_rating === "Narrow"
                    ? "#eab308"
                    : "#ef4444",
              }}
            >
              {moatAssessment.overall_rating} Moat
            </p>
          </div>
          <div className="text-right">
            <span
              className="text-xs uppercase tracking-wider"
              style={{ color: "var(--text-tertiary)" }}
            >
              Confidence
            </span>
            <p
              className="text-sm font-semibold mt-1"
              style={{ color: "var(--text-secondary)" }}
            >
              {moatAssessment.overall_confidence}
            </p>
          </div>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="flex justify-center py-4">
        <MoatRadar scores={moatScores} size={280} />
      </div>

      {/* Assessment Period */}
      <div className="text-center">
        <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
          Assessment Period: {moatAssessment.assessment_period}
        </p>
      </div>
    </div>
  );
}
