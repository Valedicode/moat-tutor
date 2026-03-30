"use client";

import React, { useState, useEffect } from "react";
import { MultiWindowReport, analyzeComprehensive } from "@/lib/moatTutorApi";
import { MoatRadar } from "./MoatRadar";

interface WindowedMoatDashboardProps {
  ticker: string;
}

type PhaseTab = "structural" | "foundation" | "acceleration" | "monetization";

export function WindowedMoatDashboard({ ticker }: WindowedMoatDashboardProps) {
  const [report, setReport] = useState<MultiWindowReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<PhaseTab>("structural");

  useEffect(() => {
    if (ticker) {
      loadComprehensiveReport();
    }
  }, [ticker]);

  const loadComprehensiveReport = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await analyzeComprehensive({
        ticker: ticker.toUpperCase(),
        includePhases: true,
      });
      setReport(data);
    } catch (err) {
      console.error("Failed to load comprehensive report:", err);
      setError(err instanceof Error ? err.message : "Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  const getActiveReport = () => {
    if (!report) return null;
    
    if (activeTab === "structural") {
      return report.structural;
    }
    
    const phaseMap: Record<string, string> = {
      foundation: "phase_foundation",
      acceleration: "phase_acceleration",
      monetization: "phase_monetization",
    };
    
    const targetLabel = phaseMap[activeTab];
    return report.phases.find((p) => p.window_label === targetLabel) || null;
  };

  const activeReport = getActiveReport();

  // Extract moat scores for radar chart
  const moatScores = activeReport?.parsed_analysis.moat_assessment
    ? {
        "Switching Costs": activeReport.parsed_analysis.moat_assessment.switching_costs.score,
        "Network Effects": activeReport.parsed_analysis.moat_assessment.network_effects.score,
        "Intangible Assets": activeReport.parsed_analysis.moat_assessment.intangible_assets.score,
        "Cost Advantages": activeReport.parsed_analysis.moat_assessment.cost_advantages.score,
        "Efficient Scale": activeReport.parsed_analysis.moat_assessment.efficient_scale.score,
      }
    : null;

  const tabs: Array<{ id: PhaseTab; label: string; description: string }> = [
    { id: "structural", label: "Structural (2000-2025)", description: "20+ year comprehensive view" },
    { id: "foundation", label: "Foundation (2000-2010)", description: "Early moat formation" },
    { id: "acceleration", label: "Acceleration (2019-2021)", description: "Stress test & competition" },
    { id: "monetization", label: "Monetization (2022-2025)", description: "Pricing power & scale" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600 font-medium">Error loading windowed analysis</p>
        <p className="text-sm text-red-500 mt-1">{error}</p>
        <button
          onClick={loadComprehensiveReport}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-6 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-gray-600">No windowed analysis available.</p>
        <button
          onClick={loadComprehensiveReport}
          className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Load Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                pb-3 px-3 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab.id
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }
              `}
            >
              <div>{tab.label}</div>
              <div className="text-xs font-normal mt-0.5">{tab.description}</div>
            </button>
          ))}
        </nav>
      </div>

      {/* Active Window Content */}
      {activeReport && (
        <div className="space-y-4">
          {/* Window Guidance */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
            <p className="text-blue-800">{activeReport.guidance}</p>
          </div>

          {/* Moat Rating/Direction */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Overall Assessment</h3>
              {activeReport.allows_rating && activeReport.parsed_analysis.moat_assessment ? (
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {activeReport.parsed_analysis.moat_assessment.overall_rating} Moat
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Confidence: {activeReport.parsed_analysis.moat_assessment.overall_confidence}
                  </div>
                  <div className="text-sm text-gray-600">
                    Score: {activeReport.parsed_analysis.moat_assessment.overall_score.toFixed(1)}/5.0
                  </div>
                </div>
              ) : (
                <div className="text-lg font-semibold text-gray-700">
                  {activeReport.output_mode === "direction" ? "Direction Only" : "Signals Only"}
                </div>
              )}
            </div>

            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Window Details</h3>
              <div className="text-sm text-gray-700">
                <div>Period: {activeReport.start_date} to {activeReport.end_date}</div>
                <div>Duration: {activeReport.duration_years.toFixed(1)} years</div>
                <div>Output Mode: {activeReport.output_mode}</div>
              </div>
            </div>
          </div>

          {/* Moat Radar Chart */}
          {moatScores && (
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Moat Dimensions</h3>
              <MoatRadar data={moatScores} />
            </div>
          )}

          {/* Executive Summary */}
          {activeReport.parsed_analysis.summary && (
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Executive Takeaway</h3>
              <p className="text-gray-700">{activeReport.parsed_analysis.summary}</p>
            </div>
          )}

          {/* Full Analysis */}
          {activeReport.parsed_analysis.raw_response && (
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Full Analysis</h3>
              <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                {activeReport.parsed_analysis.raw_response}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Synthesis (shown for structural tab) */}
      {activeTab === "structural" && report.synthesis && (
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <h3 className="text-sm font-medium text-purple-900 mb-2">Cross-Window Synthesis</h3>
          <div className="prose prose-sm max-w-none text-purple-800 whitespace-pre-wrap">
            {report.synthesis}
          </div>
        </div>
      )}
    </div>
  );
}
