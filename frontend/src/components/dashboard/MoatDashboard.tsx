"use client";

export function MoatDashboard() {
  return (
    <div
      className="flex h-full flex-col gap-6 rounded-[36px] border p-6"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "color-mix(in srgb, var(--surface) 75%, transparent)",
      }}
    >
      {/* Header Alert */}
      <div className="rounded-2xl border p-4" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
        <h2 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--risk)" }}>
          Moat Erosion Alert: Regulatory Risk
        </h2>
      </div>

      {/* Main Content Grid */}
      <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Stock Chart */}
        <div className="flex flex-col gap-3">
          <div className="relative h-64 rounded-xl border p-4" style={{ borderColor: "var(--border)", backgroundColor: "var(--background)" }}>
            <svg viewBox="0 0 400 200" className="h-full w-full" preserveAspectRatio="none">
              <defs>
                {/* Gradient for area fill */}
                <linearGradient id="priceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="var(--risk)" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="var(--risk)" stopOpacity="0" />
                </linearGradient>
              </defs>
              
              {/* Grid lines */}
              <line x1="0" y1="40" x2="400" y2="40" stroke="currentColor" strokeWidth="0.5" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              <line x1="0" y1="80" x2="400" y2="80" stroke="currentColor" strokeWidth="0.5" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              <line x1="0" y1="120" x2="400" y2="120" stroke="currentColor" strokeWidth="0.5" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              <line x1="0" y1="160" x2="400" y2="160" stroke="currentColor" strokeWidth="0.5" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              
              {/* Candlestick chart */}
              {/* Green candles - before drop */}
              <rect x="20" y="65" width="8" height="15" fill="#10b981" />
              <line x1="24" y1="60" x2="24" y2="85" stroke="#10b981" strokeWidth="1.5" />
              
              <rect x="40" y="55" width="8" height="20" fill="#10b981" />
              <line x1="44" y1="50" x2="44" y2="80" stroke="#10b981" strokeWidth="1.5" />
              
              <rect x="60" y="50" width="8" height="18" fill="#10b981" />
              <line x1="64" y1="45" x2="64" y2="73" stroke="#10b981" strokeWidth="1.5" />
              
              <rect x="80" y="48" width="8" height="22" fill="#10b981" />
              <line x1="84" y1="42" x2="84" y2="75" stroke="#10b981" strokeWidth="1.5" />
              
              {/* Red candles - the drop */}
              <rect x="100" y="70" width="8" height="30" fill="#ef4444" />
              <line x1="104" y1="65" x2="104" y2="105" stroke="#ef4444" strokeWidth="1.5" />
              
              <rect x="120" y="85" width="8" height="35" fill="#ef4444" />
              <line x1="124" y1="80" x2="124" y2="125" stroke="#ef4444" strokeWidth="1.5" />
              
              <rect x="140" y="95" width="8" height="28" fill="#ef4444" />
              <line x1="144" y1="90" x2="144" y2="128" stroke="#ef4444" strokeWidth="1.5" />
              
              {/* Recovery attempts */}
              <rect x="160" y="105" width="8" height="15" fill="#10b981" />
              <line x1="164" y1="100" x2="164" y2="125" stroke="#10b981" strokeWidth="1.5" />
              
              <rect x="180" y="100" width="8" height="12" fill="#ef4444" />
              <line x1="184" y1="95" x2="184" y2="117" stroke="#ef4444" strokeWidth="1.5" />
              
              <rect x="200" y="108" width="8" height="10" fill="#10b981" />
              <line x1="204" y1="103" x2="204" y2="123" stroke="#10b981" strokeWidth="1.5" />
              
              {/* Price line overlay */}
              <polyline
                points="24,72 44,65 64,59 84,57 104,82 124,107 144,109 164,112 184,106 204,113"
                fill="none"
                stroke="var(--risk)"
                strokeWidth="2"
                opacity="0.8"
              />
              
              {/* Area fill under line */}
              <polygon
                points="24,72 44,65 64,59 84,57 104,82 124,107 144,109 164,112 184,106 204,113 204,200 24,200"
                fill="url(#priceGradient)"
              />
              
              {/* Vertical marker line for event */}
              <line x1="104" y1="0" x2="104" y2="200" stroke="var(--risk)" strokeWidth="2" strokeDasharray="4 4" opacity="0.5" />
            </svg>
            
            {/* Y-axis labels overlay */}
            <div className="absolute left-2 top-4 flex flex-col justify-between" style={{ height: "calc(100% - 3rem)" }}>
              <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>$500</span>
              <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>$450</span>
              <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>$400</span>
            </div>
            
            {/* Bottom info */}
            <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between">
              <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>JAN 3, 2024</span>
              <span className="text-xs font-semibold" style={{ color: "var(--risk)" }}>▼ -5.6%</span>
            </div>
          </div>
          
          <div className="rounded-xl border p-3 text-center" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
            <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-secondary)" }}>
              Government announce chip export restrictions
            </p>
          </div>
        </div>

        {/* Moat Radar */}
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border p-6" style={{ borderColor: "var(--border)", backgroundColor: "var(--background)" }}>
          <div className="relative h-48 w-48">
            {/* Pentagon shape - simplified representation */}
            <svg viewBox="0 0 200 200" className="h-full w-full">
              {/* Background grid circles */}
              <circle cx="100" cy="100" r="80" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              <circle cx="100" cy="100" r="60" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              <circle cx="100" cy="100" r="40" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              <circle cx="100" cy="100" r="20" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" style={{ color: "var(--text-tertiary)" }} />
              
              {/* Pentagon data visualization */}
              <polygon
                points="100,20 175,65 155,145 45,145 25,65"
                fill="url(#radarGradient)"
                stroke="var(--accent)"
                strokeWidth="2"
                opacity="0.6"
              />
              
              {/* Gradient definition */}
              <defs>
                <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="25%" stopColor="#84cc16" />
                  <stop offset="50%" stopColor="#eab308" />
                  <stop offset="75%" stopColor="#f97316" />
                  <stop offset="100%" stopColor="#ef4444" />
                </linearGradient>
              </defs>
              
              {/* Center point */}
              <circle cx="100" cy="100" r="4" fill="var(--accent)" />
            </svg>
          </div>
          
          <div className="text-center">
            <p className="text-xs uppercase tracking-[0.3em]" style={{ color: "var(--text-secondary)" }}>
              Moat Radar
            </p>
          </div>
          
          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#10b981" }}></div>
              <span style={{ color: "var(--text-tertiary)" }}>Network Effect</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#eab308" }}></div>
              <span style={{ color: "var(--text-tertiary)" }}>Intangible Assets</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "#ef4444" }}></div>
              <span style={{ color: "var(--text-tertiary)" }}>Cost Advantage</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Explanation */}
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border)", backgroundColor: "var(--border-subtle)" }}>
        <h3 className="text-xs font-semibold uppercase tracking-[0.3em]" style={{ color: "var(--text-secondary)" }}>
          AI-Powered Explanation
        </h3>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
          On January 3, 2024, Nvidia's stock price dropped due to new government regulations raising chip exports. This erodes{" "}
          <span className="font-semibold" style={{ color: "var(--accent)" }}>
            Nvidia's Intangible Assets
          </span>{" "}
          moats, regulatory licenses, by limiting access to key markets.
        </p>
      </div>
    </div>
  );
}

