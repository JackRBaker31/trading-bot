import React from "react";

import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  GitBranch,
  RefreshCw,
  ShieldX,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DecisionTrace,
} from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";


function displayName(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


export function DecisionTimelinePanel({
  trace,
  refreshing,
  onRefresh,
}: {
  trace: DecisionTrace;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const noTrade =
    trace.decision === "NO_TRADE";

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="decision-timeline-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "rounded-lg border p-2",
              noTrade
                ? "border-amber-500/25 bg-amber-500/10 text-amber-400"
                : "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
            )}
          >
            <GitBranch className="h-5 w-5" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-medium">
                Decision Timeline
              </h3>

              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                  noTrade
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
                )}
              >
                {displayName(
                  trace.decision,
                )}
              </span>
            </div>

            <p className="mt-1 text-xs text-muted-foreground">
              {trace.summary}
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

          Capture Decision
        </Button>
      </div>

      <div className="mt-6 space-y-0">
        {trace.stages.map(
          (stage, index) => {
            const passed =
              stage.status === "PASS";

            const isLast =
              index ===
              trace.stages.length -
                1;

            return (
              <div
                key={
                  `${stage.sequence}-` +
                  stage.stage
                }
                className="relative flex gap-4"
              >
                {!isLast && (
                  <div className="absolute left-[15px] top-8 h-[calc(100%-4px)] w-px bg-border" />
                )}

                <div
                  className={cn(
                    "relative z-10 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-card",
                    passed
                      ? "border-emerald-500/30 text-emerald-400"
                      : "border-amber-500/30 text-amber-400",
                  )}
                >
                  {passed ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : stage.stage ===
                    "DECISION" ? (
                    <ShieldX className="h-4 w-4" />
                  ) : (
                    <AlertTriangle className="h-4 w-4" />
                  )}
                </div>

                <div
                  className={cn(
                    "min-w-0 flex-1 pb-6",
                    isLast && "pb-0",
                  )}
                >
                  <div className="rounded-lg border border-border bg-background p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                          {displayName(
                            stage.stage,
                          )}
                        </p>

                        <p className="mt-1 text-sm font-medium">
                          {stage.title}
                        </p>
                      </div>

                      <span
                        className={cn(
                          "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                          passed
                            ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-400"
                            : "border-amber-500/25 bg-amber-500/10 text-amber-400",
                        )}
                      >
                        {stage.status}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {stage.summary}
                    </p>

                    {stage.evidence.length >
                      0 && (
                      <div className="mt-3 space-y-2">
                        {stage.evidence.map(
                          (item) => (
                            <div
                              key={item}
                              className="flex items-start gap-2 text-xs text-muted-foreground"
                            >
                              <CircleDot className="mt-0.5 h-3 w-3 shrink-0 text-primary" />

                              <span>
                                {item}
                              </span>
                            </div>
                          ),
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          },
        )}
      </div>
    </section>
  );
}
