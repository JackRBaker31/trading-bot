import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Database,
  GitCompareArrows,
  History,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { HistoricalSimilarityReport } from "@/hooks/useHistoricalSimilarity";
import { cn } from "@/lib/utils";

function displayName(value: string | null | undefined): string {
  if (!value) return "Not available";
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function metric(value: number | null | undefined, suffix = "%"): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}${suffix}`;
}

function signedMetric(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function sampleClass(sample: string): string {
  if (sample === "MEANINGFUL") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  }
  if (sample === "DEVELOPING") {
    return "border-sky-500/30 bg-sky-500/10 text-sky-400";
  }
  return "border-amber-500/30 bg-amber-500/10 text-amber-400";
}

export function HistoricalSimilarityPanel({
  symbol,
  report,
  isPending,
  isError,
}: {
  symbol: string;
  report: HistoricalSimilarityReport | undefined;
  isPending: boolean;
  isError: boolean;
}) {
  if (isPending) {
    return <Skeleton className="h-[520px]" />;
  }

  if (isError) {
    return (
      <Card className="border-destructive/30 bg-destructive/5">
        <CardContent className="flex items-start gap-3 p-5">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
          <div>
            <p className="text-sm font-semibold">Historical similarity could not be calculated</p>
            <p className="mt-1 text-sm text-muted-foreground">
              KAIRO could not build the current thesis feature vector for {symbol}. Check market-data availability and retry.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!report) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No historical-similarity report is available for {symbol}.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden">
        <CardHeader className="border-b border-border bg-muted/20">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <GitCompareArrows className="h-4 w-4 text-primary" />
                True historical similarity
              </CardTitle>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                KAIRO compared the current {report.symbol} thesis against {report.candidate_count} older decision-memory feature vectors using {report.methodology_version}.
              </p>
            </div>
            <span
              className={cn(
                "w-fit rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em]",
                sampleClass(report.sample_quality),
              )}
            >
              {displayName(report.sample_quality)} sample
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
            {[
              ["Matched cases", String(report.matched_case_count)],
              ["Measured", String(report.measured_case_count)],
              ["Avg similarity", metric(report.average_similarity_percent)],
              ["Win rate", metric(report.win_rate_percent)],
              ["Directional return", signedMetric(report.average_directional_return_percent)],
              ["Avg hold", report.average_holding_days == null ? "—" : `${report.average_holding_days.toFixed(1)}d`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-border bg-background p-4">
                <p className="text-[9px] uppercase tracking-wider text-muted-foreground">{label}</p>
                <p className="mt-2 font-mono text-xl font-bold">{value}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border bg-muted/15 p-4">
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Target horizon</p>
              <p className="mt-2 text-sm font-semibold">{report.target_horizon_days} days · {displayName(report.current_time_horizon)}</p>
            </div>
            <div className="rounded-lg border bg-muted/15 p-4">
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Current thesis</p>
              <p className="mt-2 text-sm font-semibold">{displayName(report.current_recommendation)} · {report.current_score.toFixed(1)} score</p>
            </div>
            <div className="rounded-lg border bg-muted/15 p-4">
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Primary driver</p>
              <p className="mt-2 text-sm font-semibold">{displayName(report.current_primary_driver)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {report.warnings.length > 0 && (
        <Card className="border-amber-500/25 bg-amber-500/5">
          <CardContent className="space-y-2 p-4">
            {report.warnings.map((warning) => (
              <div key={warning} className="flex items-start gap-2 text-xs leading-5 text-muted-foreground">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
                <span>{warning}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="h-4 w-4 text-primary" />
            Closest historical cases
          </CardTitle>
        </CardHeader>
        <CardContent>
          {report.cases.length === 0 ? (
            <div className="py-10 text-center">
              <Database className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-3 text-sm font-semibold">No cases passed the {report.minimum_similarity_percent.toFixed(0)}% threshold</p>
              <p className="mt-1 text-xs text-muted-foreground">
                KAIRO will populate this view as decision memory and measured outcomes grow.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {report.cases.map((item, index) => {
                const outcome = item.outcome;
                return (
                  <div key={item.decision_id} className="rounded-xl border border-border bg-background p-4">
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[10px] font-semibold text-muted-foreground">#{index + 1}</span>
                          <span className="font-mono text-sm font-bold text-primary">{item.symbol}</span>
                          <span className="rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-primary">
                            {item.similarity_percent.toFixed(1)}% similar
                          </span>
                          {item.same_symbol && (
                            <span className="rounded-full border border-sky-500/25 bg-sky-500/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-sky-400">
                              Same symbol
                            </span>
                          )}
                        </div>
                        <p className="mt-2 text-sm font-semibold">{item.headline}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {new Date(item.thesis_generated_at).toLocaleDateString("en-GB")} · {displayName(item.recommendation)} · {displayName(item.risk_tier)} risk · {displayName(item.primary_driver)} led
                        </p>
                        <Progress value={item.similarity_percent} className="mt-3 h-1.5" />
                      </div>

                      <div
                        className={cn(
                          "min-w-[190px] rounded-lg border p-3",
                          outcome?.directional_success
                            ? "border-emerald-500/25 bg-emerald-500/5"
                            : outcome
                              ? "border-destructive/25 bg-destructive/5"
                              : "border-border bg-muted/15",
                        )}
                      >
                        <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Measured outcome</p>
                        {outcome ? (
                          <div className="mt-2 flex items-center gap-2">
                            {outcome.directional_success ? (
                              <TrendingUp className="h-4 w-4 text-emerald-400" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-destructive" />
                            )}
                            <div>
                              <p className={cn("font-mono text-lg font-bold", outcome.directional_success ? "text-emerald-400" : "text-destructive")}>{signedMetric(outcome.directional_return_percent)}</p>
                              <p className="text-[10px] text-muted-foreground">Directional · {outcome.horizon_days} days</p>
                            </div>
                          </div>
                        ) : (
                          <p className="mt-2 text-sm text-muted-foreground">Not measured yet</p>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 grid gap-4 lg:grid-cols-2">
                      <div>
                        <p className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">Why it matched</p>
                        <div className="mt-2 space-y-2">
                          {(item.matching_factors.length ? item.matching_factors : ["The weighted feature vector passed the similarity threshold."]).map((factor) => (
                            <div key={factor} className="flex items-start gap-2 text-xs leading-5">
                              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                              <span>{factor}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">Material differences</p>
                        <div className="mt-2 space-y-2">
                          {(item.differing_factors.length ? item.differing_factors : ["No heavily weighted difference fell below 60% similarity."]).map((factor) => (
                            <div key={factor} className="flex items-start gap-2 text-xs leading-5 text-muted-foreground">
                              <CircleDot className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
                              <span>{factor}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="flex items-start gap-3 p-4">
          <GitCompareArrows className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-primary">Methodology</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">{report.methodology_summary}</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              Similarity is descriptive evidence, not permission to trade. Risk, graduation and execution gates remain authoritative.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
