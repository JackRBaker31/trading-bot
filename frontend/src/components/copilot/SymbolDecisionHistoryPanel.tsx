import React from "react";

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  History,
  RefreshCw,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  SymbolDecisionHistorySummary,
  SymbolDecisionMetricChange,
} from "@/hooks/useCopilot";
import {
  cn,
} from "@/lib/utils";


function ChangeCard({
  title,
  change,
  suffix = "",
  invert = false,
}: {
  title: string;
  change: (
    SymbolDecisionMetricChange
    | null
  );
  suffix?: string;
  invert?: boolean;
}) {
  if (!change) {
    return null;
  }

  const improved =
    change.direction === "IMPROVED";

  const worsened =
    change.direction === "WORSENED";

  const Icon =
    change.change > 0
      ? ArrowUpRight
      : change.change < 0
        ? ArrowDownRight
        : ArrowRight;

  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        {title}
      </p>

      <div className="mt-2 flex items-center gap-2">
        <Icon
          className={cn(
            "h-4 w-4",
            improved &&
              "text-emerald-400",
            worsened &&
              "text-destructive",
            !improved &&
              !worsened &&
              "text-muted-foreground",
          )}
        />

        <p className="text-lg font-semibold">
          {change.change > 0
            ? "+"
            : ""}
          {change.change.toFixed(
            title === "Score"
              ? 2
              : title === "Confidence"
                ? 1
                : 0,
          )}
          {suffix}
        </p>
      </div>

      <p className="mt-1 text-xs text-muted-foreground">
        {change.previous.toFixed(
          title === "Score"
            ? 2
            : title ===
                "Confidence"
              ? 1
              : 0,
        )}
        {suffix}
        {" → "}
        {change.current.toFixed(
          title === "Score"
            ? 2
            : title ===
                "Confidence"
              ? 1
              : 0,
        )}
        {suffix}
      </p>
    </div>
  );
}


export function SymbolDecisionHistoryPanel({
  summary,
  refreshing,
  onRefresh,
}: {
  summary: (
    SymbolDecisionHistorySummary
  );
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const confidenceChange =
    summary.confidence_change
      ? {
          ...summary
            .confidence_change,
          previous:
            summary
              .confidence_change
              .previous * 100,
          current:
            summary
              .confidence_change
              .current * 100,
          change:
            summary
              .confidence_change
              .change * 100,
        }
      : null;

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="symbol-decision-history-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <History className="h-5 w-5" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-medium">
                Symbol Decision History
              </h3>

              <span className="rounded-full border border-border px-2 py-0.5 font-mono text-[10px]">
                {summary.symbol}
              </span>
            </div>

            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              {summary.summary}
            </p>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw
            className={cn(
              "mr-2 h-3.5 w-3.5",
              refreshing &&
                "animate-spin",
            )}
          />

          Refresh History
        </Button>
      </div>

      {summary.comparison_available ? (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <ChangeCard
              title="Score"
              change={
                summary.score_change
              }
            />

            <ChangeCard
              title="Confidence"
              change={
                confidenceChange
              }
              suffix="%"
            />

            <ChangeCard
              title="Rank"
              change={
                summary.rank_change
              }
              invert
            />
          </div>

          {(summary.new_blockers.length >
            0 ||
            summary.cleared_blockers
              .length > 0) && (
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {summary.new_blockers
                .length > 0 && (
                <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 p-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />

                    <p className="text-sm font-medium">
                      New Blockers
                    </p>
                  </div>

                  {summary.new_blockers
                    .map(
                      (blocker) => (
                        <p
                          key={
                            blocker
                          }
                          className="mt-2 text-xs text-muted-foreground"
                        >
                          {blocker}
                        </p>
                      ),
                    )}
                </div>
              )}

              {summary
                .cleared_blockers
                .length > 0 && (
                <div className="rounded-lg border border-emerald-500/25 bg-emerald-500/5 p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />

                    <p className="text-sm font-medium">
                      Cleared Blockers
                    </p>
                  </div>

                  {summary
                    .cleared_blockers
                    .map(
                      (blocker) => (
                        <p
                          key={
                            blocker
                          }
                          className="mt-2 text-xs text-muted-foreground"
                        >
                          {blocker}
                        </p>
                      ),
                    )}
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="mt-5 rounded-lg border border-primary/20 bg-primary/5 p-4 text-sm text-muted-foreground">
          A second recorded decision is
          required before KAIRO can show
          how this symbol changed.
        </div>
      )}
    </section>
  );
}
