import React from "react";

import {
  BookOpenCheck,
  CheckCircle2,
  CircleDashed,
  RefreshCw,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  DecisionMemoryOverview,
} from "@/hooks/useDecisionMemory";
import {
  cn,
} from "@/lib/utils";


export function DecisionMemoryPanel({
  overview,
  refreshing,
  onRefresh,
}: {
  overview: DecisionMemoryOverview;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="decision-memory-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <BookOpenCheck className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Decision Memory
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Immutable investment-thesis
              journal and Decision DNA.
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

          Refresh Memory
        </Button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Decisions
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {overview.total_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Symbols
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {overview.symbol_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Executable
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {
              overview
                .executable_count
            }
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Executed
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {overview.executed_count}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {overview.latest.length > 0 ? (
          overview.latest.map(
            (record) => (
              <article
                key={record.decision_id}
                className="rounded-lg border border-border bg-background p-4"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-bold">
                        {record.symbol}
                      </span>

                      <span className="rounded-full border border-border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                        {record.recommendation
                          .replaceAll(
                            "_",
                            " ",
                          )}
                      </span>

                      {record.executed ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <CircleDashed className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>

                    <p className="mt-2 text-sm font-medium">
                      {record.headline}
                    </p>

                    <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                      {record.decision_id}
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-right">
                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        Score
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {record.score.toFixed(
                          1,
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        Confidence
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {(
                          record.confidence
                          * 100
                        ).toFixed(1)}
                        %
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
                        Coverage
                      </p>

                      <p className="mt-1 font-mono text-sm font-bold">
                        {(
                          record
                            .confidence_coverage
                          * 100
                        ).toFixed(0)}
                        %
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            ),
          )
        ) : (
          <div className="rounded-lg border border-border bg-background p-5 text-sm text-muted-foreground">
            Decision Memory is ready.
            Generate an investment thesis to
            create the first permanent record.
          </div>
        )}
      </div>
    </section>
  );
}
