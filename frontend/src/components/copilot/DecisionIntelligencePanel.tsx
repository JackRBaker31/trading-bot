import React, {
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ShieldX,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  DecisionIntelligenceReport,
  InvestmentDecision,
} from "@/hooks/useDecisionIntelligence";
import {
  cn,
} from "@/lib/utils";


function recommendationClass(
  recommendation: string,
): string {
  if (
    recommendation
    === "BUY_CANDIDATE"
  ) {
    return (
      "border-emerald-500/30 "
      + "bg-emerald-500/10 "
      + "text-emerald-400"
    );
  }

  if (
    recommendation === "WATCH"
  ) {
    return (
      "border-sky-500/30 "
      + "bg-sky-500/10 "
      + "text-sky-400"
    );
  }

  if (
    recommendation === "AVOID"
  ) {
    return (
      "border-destructive/30 "
      + "bg-destructive/10 "
      + "text-destructive"
    );
  }

  return (
    "border-amber-500/30 "
    + "bg-amber-500/10 "
    + "text-amber-400"
  );
}


function DecisionCard({
  decision,
}: {
  decision: InvestmentDecision;
}) {
  const [
    expanded,
    setExpanded,
  ] = useState(false);

  return (
    <article className="rounded-xl border border-border bg-background p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-base font-bold">
              {decision.symbol}
            </span>

            <span
              className={cn(
                "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                recommendationClass(
                  decision.recommendation,
                ),
              )}
            >
              {decision.recommendation
                .replaceAll("_", " ")}
            </span>

            <span className="rounded-full border border-border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">
              {decision.risk_tier} risk
            </span>
          </div>

          <p className="mt-2 text-sm font-medium">
            {decision.headline}
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            {decision.event_type}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 text-right">
          <div>
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
              Score
            </p>

            <p className="mt-1 font-mono text-lg font-bold">
              {decision.score.toFixed(1)}
            </p>
          </div>

          <div>
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
              Confidence
            </p>

            <p className="mt-1 font-mono text-lg font-bold">
              {(decision.confidence * 100).toFixed(1)}%
            </p>
          </div>

          <div>
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
              Position
            </p>

            <p className="mt-1 font-mono text-lg font-bold">
              £
              {decision
                .suggested_position_value
                .toFixed(0)}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{
            width:
              `${Math.min(decision.score, 100)}%`,
          }}
        />
      </div>

      {(decision.blockers.length >
        0) && (
        <div className="mt-4 rounded-lg border border-amber-500/25 bg-amber-500/5 p-3">
          <div className="flex items-center gap-2">
            <ShieldX className="h-4 w-4 text-amber-400" />

            <p className="text-xs font-semibold">
              Execution blocked
            </p>
          </div>

          <p className="mt-2 text-xs text-muted-foreground">
            {decision.blockers[0]}
          </p>
        </div>
      )}

      <button
        type="button"
        className="mt-4 flex items-center gap-2 text-xs font-medium text-primary"
        onClick={() =>
          setExpanded(
            (value) => !value,
          )
        }
      >
        {expanded ? (
          <ChevronUp className="h-3.5 w-3.5" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5" />
        )}

        {expanded
          ? "Hide score breakdown"
          : "Show score breakdown"}
      </button>

      {expanded && (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {decision.components.map(
            (component) => (
              <div
                key={component.code}
                className="rounded-lg border border-border bg-card p-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-medium">
                    {component.label}
                  </p>

                  <span className="font-mono text-xs font-bold">
                    {component.value.toFixed(1)}
                    /
                    {component.maximum.toFixed(0)}
                  </span>
                </div>

                <p className="mt-2 text-[10px] leading-relaxed text-muted-foreground">
                  {component.detail}
                </p>
              </div>
            ),
          )}
        </div>
      )}
    </article>
  );
}


export function DecisionIntelligencePanel({
  report,
  refreshing,
  onRefresh,
}: {
  report: DecisionIntelligenceReport;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const ordered = useMemo(
    () =>
      [...report.decisions].sort(
        (left, right) =>
          right.score - left.score,
      ),
    [report.decisions],
  );

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="decision-intelligence-v2-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <BrainCircuit className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Decision Intelligence v2
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Deterministic symbol scoring,
              execution gates and advisory
              position sizing.
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

          Refresh Decisions
        </Button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Decisions
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {report.decision_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Executable
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {
              report
                .executable_candidate_count
            }
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Graduation
          </p>

          <div className="mt-2 flex items-center gap-2">
            {report.graduation_eligible ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-400" />
            )}

            <p className="text-sm font-semibold">
              {report.graduation_eligible
                ? "Eligible"
                : "Blocked"}
            </p>
          </div>
        </div>
      </div>

      {report.platform_blockers.length >
        0 && (
        <div className="mt-4 rounded-lg border border-amber-500/25 bg-amber-500/5 p-4">
          <p className="text-xs font-semibold">
            Platform gate
          </p>

          <p className="mt-2 text-xs text-muted-foreground">
            {report.platform_blockers[0]}
          </p>
        </div>
      )}

      <div className="mt-5 space-y-3">
        {ordered.length > 0 ? (
          ordered.map(
            (decision) => (
              <DecisionCard
                key={decision.symbol}
                decision={decision}
              />
            ),
          )
        ) : (
          <div className="rounded-lg border border-border bg-background p-5 text-sm text-muted-foreground">
            No ranked opportunities are
            currently available.
          </div>
        )}
      </div>
    </section>
  );
}
