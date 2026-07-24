import React, {
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  RefreshCw,
  SearchCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  SymbolDecisionTrace,
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


export function SymbolDecisionPanel({
  traces,
  refreshing,
  onRefresh,
}: {
  traces: SymbolDecisionTrace[];
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const [
    selectedSymbol,
    setSelectedSymbol,
  ] = useState(
    traces[0]?.symbol ?? "",
  );

  const selected = useMemo(
    () =>
      traces.find(
        (trace) =>
          trace.symbol === selectedSymbol,
      ) ?? traces[0],
    [traces, selectedSymbol],
  );

  if (!selected) {
    return (
      <section className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-start gap-3">
          <SearchCheck className="mt-0.5 h-5 w-5 text-muted-foreground" />

          <div>
            <h3 className="text-sm font-medium">
              Symbol Decision Intelligence
            </h3>

            <p className="mt-1 text-sm text-muted-foreground">
              No ranked symbol opportunities are
              currently available.
            </p>
          </div>
        </div>
      </section>
    );
  }

  const blocked =
    selected.decision === "BLOCKED";

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="symbol-decision-panel"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "rounded-lg border p-2",
              blocked
                ? "border-amber-500/25 bg-amber-500/10 text-amber-400"
                : "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
            )}
          >
            <SearchCheck className="h-5 w-5" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-medium">
                Symbol Decision Intelligence
              </h3>

              <span className="rounded-full border border-border px-2 py-0.5 font-mono text-[10px]">
                {selected.symbol}
              </span>

              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                  blocked
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
                )}
              >
                {displayName(
                  selected.decision,
                )}
              </span>
            </div>

            <p className="mt-1 max-w-3xl text-xs leading-relaxed text-muted-foreground">
              {selected.summary}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label="Select symbol decision"
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={selected.symbol}
            onChange={(event) => {
              setSelectedSymbol(
                event.target.value,
              );
            }}
          >
            {traces.map((trace) => (
              <option
                key={trace.symbol}
                value={trace.symbol}
              >
                {trace.symbol} · #{trace.rank}
              </option>
            ))}
          </select>

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
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Rank
          </p>
          <p className="mt-2 text-xl font-semibold">
            #{selected.rank}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Opportunity Score
          </p>
          <p className="mt-2 text-xl font-semibold">
            {selected.score.toFixed(2)}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Confidence
          </p>
          <p className="mt-2 text-xl font-semibold">
            {(selected.confidence * 100).toFixed(1)}%
          </p>
        </div>

        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Classification
          </p>
          <p className="mt-2 text-xl font-semibold">
            {displayName(
              selected.classification,
            )}
          </p>
        </div>
      </div>

      <div className="mt-5 rounded-lg border border-border bg-background p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Source Evidence
        </p>
        <p className="mt-2 text-sm font-medium">
          {selected.headline}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {displayName(
            selected.event_type,
          )}
          {" · "}
          {displayName(
            selected.sentiment,
          )}
        </p>
      </div>

      <div className="mt-6 space-y-0">
        {selected.stages.map(
          (stage, index) => {
            const passed =
              stage.status === "PASS";
            const isLast =
              index ===
              selected.stages.length - 1;

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

                    {stage.evidence.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {stage.evidence.map(
                          (item) => (
                            <div
                              key={item}
                              className="flex items-start gap-2 text-xs text-muted-foreground"
                            >
                              <CircleDot className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
                              <span>{item}</span>
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
