import React from "react";

import {
  BrainCircuit,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  AdaptiveIntelligenceReport,
} from "@/hooks/useAdaptiveIntelligence";
import {
  cn,
} from "@/lib/utils";


function percentage(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return `${(value * 100).toFixed(1)}%`;
}


export function AdaptiveIntelligencePanel({
  report,
  refreshing,
  proposing,
  onRefresh,
  onPropose,
}: {
  report: AdaptiveIntelligenceReport;
  refreshing: boolean;
  proposing: boolean;
  onRefresh: () => void;
  onPropose: () => void;
}) {
  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="adaptive-intelligence-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <BrainCircuit className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Adaptive Intelligence
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Performance learning, portfolio
              optimisation, risk attribution,
              calibrated sizing and investment
              committee consensus.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
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

          <Button
            type="button"
            size="sm"
            disabled={proposing}
            onClick={onPropose}
          >
            <Sparkles
              className={cn(
                "mr-2 h-3.5 w-3.5",
                proposing &&
                  "animate-pulse",
              )}
            />

            Propose Evolution
          </Button>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
        <ShieldCheck className="h-4 w-4 text-emerald-400" />

        <p className="text-xs">
          Mode:
          {" "}
          <span className="font-semibold">
            {report.execution_mode}
          </span>
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Outcomes
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {report.performance.observation_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Positive rate
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {percentage(
              report.performance.positive_rate,
            )}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Risk
          </p>
          <p className="mt-1 text-sm font-semibold">
            {report.risk.overall_tier}
            {" "}
            ({report.risk.overall_risk_score.toFixed(0)})
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Proposals
          </p>
          <p className="mt-1 font-mono text-xl font-bold">
            {report.proposals.length}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        <div className="rounded-lg border border-border bg-background p-4">
          <h4 className="text-xs font-semibold">
            Portfolio Optimisation
          </h4>

          <div className="mt-3 space-y-2">
            {report.portfolio.allocations.length > 0 ? (
              report.portfolio.allocations.map(
                (item) => (
                  <div
                    key={item.symbol}
                    className="flex items-center justify-between rounded-lg bg-muted/30 p-3"
                  >
                    <div>
                      <p className="font-mono text-xs font-bold">
                        {item.symbol}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {(item.constrained_weight * 100)
                          .toFixed(1)}
                        % allocation
                      </p>
                    </div>

                    <p className="font-mono text-sm font-bold">
                      £
                      {item.suggested_value.toFixed(0)}
                    </p>
                  </div>
                ),
              )
            ) : (
              <p className="text-xs text-muted-foreground">
                No executable allocation is
                currently available.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <h4 className="text-xs font-semibold">
            Investment Committee
          </h4>

          <div className="mt-3 space-y-2">
            {report.committee.map(
              (item) => (
                <div
                  key={item.symbol}
                  className="flex items-center justify-between rounded-lg bg-muted/30 p-3"
                >
                  <div>
                    <p className="font-mono text-xs font-bold">
                      {item.symbol}
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      Consensus
                      {" "}
                      {item.consensus_score.toFixed(1)}
                      %
                    </p>
                  </div>

                  <span className="rounded-full border border-border px-2 py-0.5 text-[9px] font-bold uppercase">
                    {item.final_stance}
                  </span>
                </div>
              ),
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
