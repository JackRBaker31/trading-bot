import React from "react";

import {
  AlertTriangle,
  BrainCircuit,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  AdvancedIntelligenceReport,
} from "@/hooks/useAdvancedIntelligence";
import {
  cn,
} from "@/lib/utils";


export function AdvancedIntelligencePanel({
  report,
  refreshing,
  onRefresh,
}: {
  report: AdvancedIntelligenceReport;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const marketDataDegraded = ["DEGRADED", "UNAVAILABLE"].includes(
    report.market_data_health?.status?.toUpperCase() ?? "",
  );

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="advanced-intelligence-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <BrainCircuit className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Advanced Intelligence
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Regime, multi-timeframe,
              explainability and Bayesian
              confidence calibration.
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
              refreshing &&
                "animate-spin",
            )}
          />

          Refresh
        </Button>
      </div>

      {marketDataDegraded && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-500/25 bg-amber-500/5 p-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <p className="text-xs leading-relaxed text-muted-foreground">
            Market data is degraded. Cached history is preserving the available intelligence report.
          </p>
        </div>
      )}

      <div className="mt-4 flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
        <ShieldCheck className="h-4 w-4 text-emerald-400" />

        <p className="text-xs">
          {report.execution_mode}
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Regime
          </p>
          <p className="mt-1 text-sm font-semibold">
            {report.regime.regime}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Buy threshold
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {report.regime.buy_threshold.toFixed(0)}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Position factor
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {(report.regime.position_multiplier * 100)
              .toFixed(0)}
            %
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Bayesian samples
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {report.calibration.sample_count}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {report.decisions.map(
          (decision) => (
            <article
              key={decision.symbol}
              className="rounded-lg border border-border bg-background p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-sm font-bold">
                      {decision.symbol}
                    </span>

                    <span className="rounded-full border border-border px-2 py-0.5 text-[9px] font-bold uppercase">
                      {decision.recommendation}
                    </span>
                  </div>

                  <p className="mt-2 text-xs text-muted-foreground">
                    {decision.summary}
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-4 text-right">
                  <div>
                    <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                      Adjusted
                    </p>
                    <p className="mt-1 font-mono text-sm font-bold">
                      {decision.adjusted_score.toFixed(1)}
                    </p>
                  </div>

                  <div>
                    <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                      Confidence
                    </p>
                    <p className="mt-1 font-mono text-sm font-bold">
                      {(decision.calibrated_confidence * 100)
                        .toFixed(1)}
                      %
                    </p>
                  </div>

                  <div>
                    <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                      Alignment
                    </p>
                    <p className="mt-1 text-xs font-semibold">
                      {decision.timeframe_alignment}
                    </p>
                  </div>
                </div>
              </div>
            </article>
          ),
        )}
      </div>
    </section>
  );
}
