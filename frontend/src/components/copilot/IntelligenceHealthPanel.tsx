import React, {
  useState,
} from "react";

import {
  Activity,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import {
  Button,
} from "@/components/ui/button";
import {
  IntelligenceHealthOverview,
  StageDiagnostic,
} from "@/hooks/useIntelligenceObservability";
import {
  cn,
} from "@/lib/utils";


function milliseconds(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}s`;
  }

  return `${value.toFixed(0)}ms`;
}


function StageRow({
  stage,
}: {
  stage: StageDiagnostic;
}) {
  const [open, setOpen] = useState(
    false
  );

  return (
    <div className="rounded-lg border border-border bg-background">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 p-4 text-left"
        onClick={() => {
          setOpen((value) => !value);
        }}
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}

          <div>
            <p className="text-xs font-semibold">
              {stage.display_name}
            </p>

            <p className="mt-1 text-[10px] text-muted-foreground">
              {stage.event_count}
              {" "}
              operation event(s)
              {" · "}
              {milliseconds(
                stage.duration_ms,
              )}
            </p>
          </div>
        </div>

        <div className="text-right">
          <span
            className={cn(
              "text-[9px] font-bold uppercase tracking-wider",
              stage.status ===
                "SUCCEEDED"
                ? "text-emerald-400"
                : stage.status ===
                    "SUCCEEDED_WITH_WARNINGS"
                  ? "text-amber-400"
                  : "text-destructive",
            )}
          >
            {stage.status.replaceAll(
              "_",
              " ",
            )}
          </span>

          {!stage.diagnostics_complete && (
            <p className="mt-1 text-[9px] text-amber-400">
              Detail incomplete
            </p>
          )}
        </div>
      </button>

      {open && (
        <div className="border-t border-border p-4">
          {stage.warnings.length > 0 && (
            <div className="space-y-2">
              {stage.warnings.map(
                (warning) => (
                  <div
                    key={warning}
                    className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-300"
                  >
                    {warning}
                  </div>
                ),
              )}
            </div>
          )}

          <div className="mt-3 grid gap-2 sm:grid-cols-4">
            <Metric
              label="Failures"
              value={String(
                stage.failure_count,
              )}
            />
            <Metric
              label="Retries"
              value={String(
                stage.retry_count,
              )}
            />
            <Metric
              label="Recovered"
              value={String(
                stage.recovered_count,
              )}
            />
            <Metric
              label="Avg latency"
              value={milliseconds(
                stage.average_latency_ms,
              )}
            />
          </div>

          {stage.events.length > 0 && (
            <div className="mt-4 space-y-2">
              {stage.events.map(
                (event) => (
                  <div
                    key={event.event_id}
                    className="rounded-md bg-muted/30 p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-mono text-xs font-semibold">
                        {event.symbol ??
                          "PLATFORM"}
                        {" · "}
                        {event.operation}
                      </p>

                      <span className="text-[9px] font-bold uppercase">
                        {event.status}
                      </span>
                    </div>

                    <p className="mt-1 text-[10px] text-muted-foreground">
                      {event.provider ??
                        "Internal"}
                      {event.error_code
                        ? ` · ${event.error_code}`
                        : ""}
                      {event.latency_ms !==
                      null
                        ? ` · ${milliseconds(
                            event.latency_ms,
                          )}`
                        : ""}
                    </p>

                    {event.error_summary && (
                      <p className="mt-2 text-xs text-amber-300">
                        {
                          event.error_summary
                        }
                      </p>
                    )}

                    <p className="mt-2 text-[10px] text-muted-foreground">
                      Retries:
                      {" "}
                      {event.retry_count}
                      {" · "}
                      Recovered:
                      {" "}
                      {event.recovered
                        ? "Yes"
                        : "No"}
                      {" · "}
                      Cache:
                      {" "}
                      {event.cache_status ??
                        "Unknown"}
                    </p>
                  </div>
                ),
              )}
            </div>
          )}

          <details className="mt-4">
            <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Stage metrics
            </summary>

            <pre className="mt-2 overflow-auto rounded-md bg-muted/30 p-3 text-[10px]">
              {JSON.stringify(
                stage.detail,
                null,
                2,
              )}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}


function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md bg-muted/30 p-3">
      <p className="text-[9px] uppercase tracking-wider text-muted-foreground">
        {label}
      </p>

      <p className="mt-1 font-mono text-sm font-bold">
        {value}
      </p>
    </div>
  );
}


export function IntelligenceHealthPanel({
  overview,
  refreshing,
  onRefresh,
}: {
  overview: IntelligenceHealthOverview;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const latest = overview.recent_jobs[0];

  return (
    <section
      className="rounded-xl border border-border bg-card p-5"
      data-testid="intelligence-health-panel"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
            <Activity className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-medium">
              Intelligence Health
            </h3>

            <p className="mt-1 text-xs text-muted-foreground">
              Stage diagnostics, retries,
              provider latency and recovery.
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

      <div className="mt-5 grid gap-3 sm:grid-cols-4">
        <Metric
          label="Health"
          value={overview.health_status}
        />
        <Metric
          label="Jobs with warnings"
          value={String(
            overview.warning_count,
          )}
        />
        <Metric
          label="Operation failures"
          value={String(
            overview.operation_failure_count,
          )}
        />
        <Metric
          label="Recovered"
          value={String(
            overview.recovered_operation_count,
          )}
        />
      </div>

      {overview.attention_items.length >
        0 && (
        <div className="mt-4 space-y-2">
          {overview.attention_items.map(
            (item) => (
              <div
                key={item}
                className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3"
              >
                <ShieldAlert className="mt-0.5 h-4 w-4 text-amber-400" />

                <p className="text-xs text-amber-300">
                  {item}
                </p>
              </div>
            ),
          )}
        </div>
      )}

      {latest && (
        <div className="mt-5">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold">
                Latest Intelligence Cycle
              </h4>

              <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                {latest.job_id}
              </p>
            </div>

            <span className="text-[9px] font-bold uppercase tracking-wider">
              {latest.status.replaceAll(
                "_",
                " ",
              )}
            </span>
          </div>

          <div className="space-y-2">
            {latest.stages.map(
              (stage) => (
                <StageRow
                  key={stage.stage}
                  stage={stage}
                />
              ),
            )}
          </div>
        </div>
      )}
    </section>
  );
}
