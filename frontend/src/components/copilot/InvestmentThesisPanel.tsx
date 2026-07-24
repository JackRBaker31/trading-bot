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
  CircleDashed,
  RefreshCw,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  InvestmentThesis,
  InvestmentThesisReport,
} from "@/hooks/useInvestmentTheses";
import {
  cn,
} from "@/lib/utils";


function ThesisCard({
  thesis,
}: {
  thesis: InvestmentThesis;
}) {
  const [
    expanded,
    setExpanded,
  ] = useState(false);

  return (
    <article className="rounded-xl border border-border bg-background p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-base font-bold">
              {thesis.symbol}
            </span>

            <span
              className={cn(
                "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                thesis.recommendation
                  === "BUY_CANDIDATE"
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : thesis.recommendation
                    === "INCOMPLETE"
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                    : "border-border text-muted-foreground",
              )}
            >
              {thesis.recommendation
                .replaceAll("_", " ")}
            </span>

            <span className="rounded-full border border-border px-2 py-0.5 text-[9px] uppercase tracking-wider text-muted-foreground">
              {thesis.time_horizon}
            </span>
          </div>

          <p className="mt-2 text-sm font-medium">
            {thesis.headline}
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            Primary driver:
            {" "}
            {thesis.primary_driver}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 text-right">
          <div>
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
              Thesis score
            </p>

            <p className="mt-1 font-mono text-lg font-bold">
              {thesis.score.toFixed(1)}
            </p>
          </div>

          <div>
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
              Confidence
            </p>

            <p className="mt-1 font-mono text-lg font-bold">
              {(thesis.confidence * 100)
                .toFixed(1)}
              %
            </p>
          </div>

          <div>
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
              Coverage
            </p>

            <p className="mt-1 font-mono text-lg font-bold">
              {(thesis
                .confidence_coverage
                * 100)
                .toFixed(0)}
              %
            </p>
          </div>
        </div>
      </div>

      {thesis.blockers.length > 0 && (
        <div className="mt-4 rounded-lg border border-amber-500/25 bg-amber-500/5 p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />

            <p className="text-xs font-semibold">
              Thesis incomplete
            </p>
          </div>

          <p className="mt-2 text-xs text-muted-foreground">
            {thesis.blockers[0]}
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
          ? "Hide capability detail"
          : "Show capability detail"}
      </button>

      {expanded && (
        <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
          {thesis.capabilities.map(
            (capability) => (
              <div
                key={capability.capability}
                className="rounded-lg border border-border bg-card p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold">
                    {capability.capability}
                  </p>

                  {capability.status
                    === "AVAILABLE" ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <CircleDashed className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>

                <p className="mt-2 font-mono text-sm font-bold">
                  {capability.score
                    === null
                    ? "Unavailable"
                    : `${capability.score.toFixed(1)} / ${capability.maximum.toFixed(0)}`}
                </p>

                <p className="mt-2 text-[10px] leading-relaxed text-muted-foreground">
                  {capability.summary}
                </p>
              </div>
            ),
          )}
        </div>
      )}
    </article>
  );
}


export function InvestmentThesisPanel({
  report,
  refreshing,
  onRefresh,
}: {
  report: InvestmentThesisReport;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const theses = useMemo(
    () =>
      [...report.theses].sort(
        (left, right) =>
          right.score - left.score,
      ),
    [report.theses],
  );

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="investment-thesis-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <BrainCircuit className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Decision Intelligence v3
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Multi-capability investment
              theses with explicit data
              coverage.
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

          Refresh Theses
        </Button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Theses
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {report.thesis_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Executable
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {report.executable_count}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
            Capabilities online
          </p>

          <p className="mt-1 font-mono text-xl font-bold">
            {
              report
                .complete_capability_count
            }
            /
            {
              report
                .required_capability_count
            }
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {theses.map(
          (thesis) => (
            <ThesisCard
              key={thesis.thesis_id}
              thesis={thesis}
            />
          ),
        )}
      </div>
    </section>
  );
}
