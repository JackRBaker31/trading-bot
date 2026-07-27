import React from "react";

import { AlertTriangle, Globe2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MacroAnalysis } from "@/hooks/useMacroAnalysis";
import { cn } from "@/lib/utils";


export function MacroAnalysisPanel({
  analysis,
  refreshing,
  onRefresh,
}: {
  analysis: MacroAnalysis;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const marketDataDegraded = ["DEGRADED", "UNAVAILABLE"].includes(
    analysis.market_data_health?.status?.toUpperCase() ?? "",
  );

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="macro-analysis-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <Globe2 className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Macro Capability
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Market regime as of {analysis.as_of_date}
            </p>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={refreshing}
          onClick={onRefresh}
        >
          <RefreshCw
            className={cn(
              "mr-2 h-3.5 w-3.5",
              refreshing && "animate-spin",
            )}
          />
          Refresh Macro
        </Button>
      </div>

      {marketDataDegraded && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-500/25 bg-amber-500/5 p-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <p className="text-xs leading-relaxed text-muted-foreground">
            Market data is degraded. KAIRO is using cached historical data where available.
          </p>
        </div>
      )}

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Score
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {analysis.score.toFixed(1)}/{analysis.maximum.toFixed(0)}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Regime
          </p>
          <p className="mt-1 text-sm font-semibold">
            {analysis.regime}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Confidence
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {(analysis.confidence * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
        {analysis.metrics.map((metric) => (
          <div
            key={metric.code}
            className="rounded-lg border border-border bg-background p-4"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold">
                {metric.label}
              </p>
              <span className="font-mono text-xs font-bold">
                {metric.score.toFixed(1)}/{metric.maximum.toFixed(0)}
              </span>
            </div>

            <p className="mt-2 text-sm font-medium">
              {metric.stance}
            </p>
            <p className="mt-1 text-[10px] text-muted-foreground">
              {metric.display_value}
            </p>
            <p className="mt-2 text-[10px] leading-relaxed text-muted-foreground">
              {metric.detail}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
