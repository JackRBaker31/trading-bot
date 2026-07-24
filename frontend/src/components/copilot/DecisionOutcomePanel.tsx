import React from "react";

import {
  Activity,
  RefreshCw,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  DecisionOutcomeOverview,
} from "@/hooks/useDecisionOutcomes";
import {
  cn,
} from "@/lib/utils";


function percent(
  value: number,
): string {
  return `${value >= 0 ? "+" : ""}${(
    value * 100
  ).toFixed(2)}%`;
}


export function DecisionOutcomePanel({
  overview,
  refreshing,
  capturing,
  onRefresh,
  onCapture,
}: {
  overview: DecisionOutcomeOverview;
  refreshing: boolean;
  capturing: boolean;
  onRefresh: () => void;
  onCapture: () => void;
}) {
  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="decision-outcome-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <Activity className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Outcome Tracking
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Immutable horizon returns,
              benchmark alpha and excursion
              tracking.
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
            disabled={capturing}
            onClick={onCapture}
          >
            <RefreshCw
              className={cn(
                "mr-2 h-3.5 w-3.5",
                capturing &&
                  "animate-spin",
              )}
            />

            Capture Due Outcomes
          </Button>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Decisions tracked
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {
              overview
                .tracked_decision_count
            }
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Observations
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {overview.observation_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Average return
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {overview.average_return
              === null
              ? "—"
              : percent(
                  overview.average_return,
                )}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Average alpha
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {overview.average_alpha
              === null
              ? "—"
              : percent(
                  overview.average_alpha,
                )}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {overview.latest.length > 0 ? (
          overview.latest.map(
            (item) => (
              <article
                key={item.outcome_id}
                className="rounded-lg border border-border bg-background p-4"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-bold">
                        {item.symbol}
                      </span>

                      <span className="rounded-full border border-border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                        {item.horizon_days}
                        D
                      </span>

                      <span
                        className={cn(
                          "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                          item.status
                            === "POSITIVE"
                            ? "border-emerald-500/30 text-emerald-400"
                            : item.status
                              === "NEGATIVE"
                              ? "border-destructive/30 text-destructive"
                              : "border-border text-muted-foreground",
                        )}
                      >
                        {item.status}
                      </span>
                    </div>

                    <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                      {item.decision_id}
                    </p>
                  </div>

                  <div className="grid grid-cols-4 gap-4 text-right">
                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        Return
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {percent(
                          item.absolute_return,
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        Alpha
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {percent(item.alpha)}
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        MFE
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {percent(
                          item
                            .maximum_favourable_excursion,
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        Drawdown
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {percent(
                          item.maximum_drawdown,
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            ),
          )
        ) : (
          <div className="rounded-lg border border-border bg-background p-5 text-sm text-muted-foreground">
            No outcome horizons are due yet.
          </div>
        )}
      </div>
    </section>
  );
}
