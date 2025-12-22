"use client";

import { useState } from "react";

export interface MoatScores {
  networkEffects: number; // 0-5
  switchingCosts: number; // 0-5
  intangibleAssets: number; // 0-5
  costAdvantages: number; // 0-5
  efficientScale: number; // 0-5
}

interface MoatRadarProps {
  scores: MoatScores;
  size?: number;
  className?: string;
}

const MOAT_LABELS = [
  { key: "networkEffects", label: "Network Effects", shortLabel: "Network" },
  { key: "intangibleAssets", label: "Intangible Assets", shortLabel: "Intangible" },
  { key: "costAdvantages", label: "Cost Advantages", shortLabel: "Cost" },
  { key: "efficientScale", label: "Efficient Scale", shortLabel: "Efficient" },
  { key: "switchingCosts", label: "Switching Costs", shortLabel: "Switching" },
];

export function MoatRadar({ scores, size = 240, className = "" }: MoatRadarProps) {
  const [hoveredPoint, setHoveredPoint] = useState<string | null>(null);

  // Calculate average moat score
  const averageScore =
    (scores.networkEffects +
      scores.switchingCosts +
      scores.intangibleAssets +
      scores.costAdvantages +
      scores.efficientScale) /
    5;

  // Pentagon parameters
  const centerX = size / 2;
  const centerY = size / 2;
  const maxRadius = size * 0.35; // 35% of size for outer ring
  const numSides = 5;

  // Calculate pentagon points for a given radius
  const getPentagonPoints = (radius: number) => {
    const points: { x: number; y: number }[] = [];
    for (let i = 0; i < numSides; i++) {
      // Start from top and go clockwise
      const angle = (Math.PI * 2 * i) / numSides - Math.PI / 2;
      points.push({
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      });
    }
    return points;
  };

  // Generate grid rings
  const gridLevels = [1, 2, 3, 4, 5];
  const gridRings = gridLevels.map((level) => {
    const radius = (maxRadius * level) / 5;
    const points = getPentagonPoints(radius);
    return points.map((p) => `${p.x},${p.y}`).join(" ");
  });

  // Generate data polygon based on scores
  const dataPoints = MOAT_LABELS.map((item, i) => {
    const score = scores[item.key as keyof MoatScores];
    const radius = (maxRadius * score) / 5;
    const angle = (Math.PI * 2 * i) / numSides - Math.PI / 2;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      score,
      label: item.label,
      key: item.key,
    };
  });

  const dataPolygonPoints = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Generate axis lines from center to outer vertices
  const outerPoints = getPentagonPoints(maxRadius);
  const axisLines = outerPoints.map((point, i) => ({
    x1: centerX,
    y1: centerY,
    x2: point.x,
    y2: point.y,
    label: MOAT_LABELS[i],
  }));

  // Label positions (slightly outside the outer ring)
  const labelRadius = maxRadius * 1.25;
  const labelPositions = MOAT_LABELS.map((item, i) => {
    const angle = (Math.PI * 2 * i) / numSides - Math.PI / 2;
    return {
      x: centerX + labelRadius * Math.cos(angle),
      y: centerY + labelRadius * Math.sin(angle),
      label: item.shortLabel,
      fullLabel: item.label,
      key: item.key,
    };
  });

  // Get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 4.5) return "#10b981"; // Excellent - green
    if (score >= 3.5) return "#84cc16"; // Good - lime
    if (score >= 2.5) return "#eab308"; // Moderate - yellow
    if (score >= 1.5) return "#f97316"; // Weak - orange
    return "#ef4444"; // Very weak - red
  };

  const overallColor = getScoreColor(averageScore);

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {/* Moat Score Display */}
      <div className="text-center">
        <p
          className="text-xs uppercase tracking-[0.3em]"
          style={{ color: "var(--text-secondary)" }}
        >
          Overall Moat Score
        </p>
        <p
          className="mt-2 text-4xl font-bold"
          style={{ color: overallColor }}
        >
          {averageScore.toFixed(1)}
          <span className="text-lg font-normal" style={{ color: "var(--text-tertiary)" }}>
            /5.0
          </span>
        </p>
        <p
          className="mt-1 text-xs"
          style={{ color: "var(--text-tertiary)" }}
        >
          {averageScore >= 4.5
            ? "Exceptional Moat"
            : averageScore >= 3.5
            ? "Strong Moat"
            : averageScore >= 2.5
            ? "Moderate Moat"
            : averageScore >= 1.5
            ? "Weak Moat"
            : "No Significant Moat"}
        </p>
      </div>

      {/* Radar Chart */}
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="overflow-visible"
      >
        {/* Grid rings */}
        {gridRings.map((points, i) => (
          <polygon
            key={i}
            points={points}
            fill="none"
            stroke="var(--text-tertiary)"
            strokeWidth="1.5"
            opacity={0.5}
          />
        ))}

        {/* Axis lines */}
        {axisLines.map((line, i) => (
          <line
            key={i}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke="var(--text-tertiary)"
            strokeWidth="1.5"
            opacity={0.4}
          />
        ))}

        {/* Data polygon with gradient */}
        <defs>
          <linearGradient
            id="moatGradient"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="100%"
          >
            <stop offset="0%" stopColor={overallColor} stopOpacity={0.4} />
            <stop offset="100%" stopColor={overallColor} stopOpacity={0.1} />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Data area */}
        <polygon
          points={dataPolygonPoints}
          fill="url(#moatGradient)"
          stroke={overallColor}
          strokeWidth="2"
          opacity={0.8}
          filter="url(#glow)"
        />

        {/* Data points */}
        {dataPoints.map((point, i) => (
          <g key={i}>
            <circle
              cx={point.x}
              cy={point.y}
              r={hoveredPoint === point.key ? 6 : 4}
              fill={getScoreColor(point.score)}
              stroke="var(--background)"
              strokeWidth="2"
              style={{
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={() => setHoveredPoint(point.key)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
            {hoveredPoint === point.key && (
              <g>
                {/* Tooltip background */}
                <rect
                  x={point.x - 35}
                  y={point.y - 35}
                  width="70"
                  height="25"
                  rx="4"
                  fill="var(--surface)"
                  stroke="var(--border)"
                  strokeWidth="1"
                  opacity="0.95"
                />
                {/* Tooltip text */}
                <text
                  x={point.x}
                  y={point.y - 25}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="600"
                  fill="var(--text-primary)"
                >
                  {point.score.toFixed(1)}/5.0
                </text>
              </g>
            )}
          </g>
        ))}

        {/* Labels */}
        {labelPositions.map((pos, i) => (
          <text
            key={i}
            x={pos.x}
            y={pos.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="11"
            fontWeight="500"
            fill="var(--text-secondary)"
            style={{
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={() => setHoveredPoint(pos.key)}
            onMouseLeave={() => setHoveredPoint(null)}
          >
            {pos.label}
          </text>
        ))}
      </svg>

      {/* Score Legend */}
      <div className="grid grid-cols-5 gap-2 text-xs">
        {MOAT_LABELS.map((item) => {
          const score = scores[item.key as keyof MoatScores];
          return (
            <div
              key={item.key}
              className="flex flex-col items-center gap-1 rounded-lg p-2 transition-all"
              style={{
                backgroundColor:
                  hoveredPoint === item.key
                    ? "var(--border-subtle)"
                    : "transparent",
                cursor: "pointer",
              }}
              onMouseEnter={() => setHoveredPoint(item.key)}
              onMouseLeave={() => setHoveredPoint(null)}
            >
              <div
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: getScoreColor(score) }}
              />
              <span
                className="text-center leading-tight"
                style={{ color: "var(--text-tertiary)" }}
              >
                {item.shortLabel}
              </span>
              <span
                className="font-semibold"
                style={{ color: getScoreColor(score) }}
              >
                {score.toFixed(1)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

