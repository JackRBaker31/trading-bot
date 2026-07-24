import React from "react";

import {
  AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight,
  CheckCircle2, History, RefreshCw, TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  CopilotChangeSummary, CopilotMetricChange,
} from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";


function Metric({
  title, change, suffix = "",
}: {
  title: string;
  change: CopilotMetricChange | null;
  suffix?: string;
}) {
  if (!change) return null;

  const Icon =
    change.direction === "UP"
      ? ArrowUpRight
      : change.direction === "DOWN"
        ? ArrowDownRight
        : ArrowRight;

  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
        {title}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <Icon className={cn(
          "h-4 w-4",
          change.direction === "UP" && "text-emerald-400",
          change.direction === "DOWN" && "text-destructive",
          change.direction === "UNCHANGED" && "text-muted-foreground",
        )} />
        <p className="text-lg font-semibold">
          {change.change > 0 ? "+" : ""}
          {change.change.toFixed(suffix === "%" ? 1 : 0)}
          {suffix}
        </p>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {change.previous.toFixed(suffix === "%" ? 1 : 0)}
        {suffix}{" → "}
        {change.current.toFixed(suffix === "%" ? 1 : 0)}
        {suffix}
      </p>
    </div>
  );
}


export function ChangeIntelligencePanel({
  summary, refreshing, onRefresh,
}: {
  summary: CopilotChangeSummary;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="change-intelligence-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <History className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-medium">What Changed</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Decision intelligence compared with the previous snapshot.
            </p>
          </div>
        </div>
        <Button
          type="button" variant="outline" size="sm"
          onClick={onRefresh} disabled={refreshing}
        >
          <RefreshCw className={cn(
            "mr-2 h-3.5 w-3.5",
            refreshing && "animate-spin",
          )} />
          Capture & Compare
        </Button>
      </div>

      <div className="mt-5 rounded-lg border border-border bg-background p-4">
        <div className="flex items-start gap-3">
          <TrendingUp className="mt-0.5 h-4 w-4 text-[#D4AF37]" />
          <p className="text-sm leading-relaxed">{summary.summary}</p>
        </div>
      </div>

      {summary.comparison_available ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric title="Confidence" change={summary.confidence_change} suffix="%" />
            <Metric title="Total Signals" change={summary.signal_count_change} />
            <Metric title="Actionable Signals" change={summary.actionable_signal_change} />
            <Metric title="Graduation Checks" change={summary.graduation_passed_change} />
          </div>

          {(summary.new_blockers.length > 0 ||
            summary.cleared_blockers.length > 0) && (
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {summary.new_blockers.length > 0 && (
                <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 p-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    <p className="text-sm font-medium">New Blockers</p>
                  </div>
                  {summary.new_blockers.map((item) => (
                    <p key={item} className="mt-2 text-xs text-muted-foreground">
                      {item}
                    </p>
                  ))}
                </div>
              )}
              {summary.cleared_blockers.length > 0 && (
                <div className="rounded-lg border border-emerald-500/25 bg-emerald-500/5 p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <p className="text-sm font-medium">Cleared Blockers</p>
                  </div>
                  {summary.cleared_blockers.map((item) => (
                    <p key={item} className="mt-2 text-xs text-muted-foreground">
                      {item}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-4 text-sm text-muted-foreground">
          A second snapshot is required before KAIRO can calculate changes.
        </div>
      )}
    </section>
  );
}
