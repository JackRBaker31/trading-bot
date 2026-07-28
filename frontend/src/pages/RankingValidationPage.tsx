import { useState } from "react";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  FlaskConical,
  Gauge,
  RefreshCw,
  Scale,
  Target,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  OpportunityValidationBucket,
  RankingValidationHorizon,
  useRankingValidation,
} from "@/hooks/useRankingValidation";
import { cn } from "@/lib/utils";

function percent(value: number | null, digits = 1): string {
  return value === null ? "—" : `${value.toFixed(digits)}%`;
}

function number(value: number | null, digits = 2): string {
  return value === null ? "—" : value.toFixed(digits);
}

function returnClass(value: number | null): string {
  if (value === null) return "text-muted-foreground";
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-rose-400";
  return "text-muted-foreground";
}

function maturityClass(value: string): string {
  if (value === "MATURE") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  }
  if (value === "DEVELOPING") {
    return "border-sky-500/30 bg-sky-500/10 text-sky-400";
  }
  return "border-amber-500/30 bg-amber-500/10 text-amber-400";
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
          {label}
        </p>
        <p className="mt-2 font-mono text-2xl font-black">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  );
}

function BucketTable({
  title,
  icon: Icon,
  items,
}: {
  title: string;
  icon: typeof BarChart3;
  items: OpportunityValidationBucket[];
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Icon className="h-4 w-4 text-primary" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-xs">
            <thead className="border-b text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="pb-2 pr-4">Group</th>
                <th className="pb-2 pr-4 text-right">Sample</th>
                <th className="pb-2 pr-4 text-right">Hit rate</th>
                <th className="pb-2 pr-4 text-right">Avg return</th>
                <th className="pb-2 pr-4 text-right">Median</th>
                <th className="pb-2 text-right">Avg alpha</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.code} className="border-b border-border/60 last:border-0">
                  <td className="py-3 pr-4 font-semibold">{item.label}</td>
                  <td className="py-3 pr-4 text-right font-mono">{item.sample_count}</td>
                  <td className="py-3 pr-4 text-right font-mono">
                    {percent(item.hit_rate_percent)}
                  </td>
                  <td
                    className={cn(
                      "py-3 pr-4 text-right font-mono font-bold",
                      returnClass(item.average_return_percent),
                    )}
                  >
                    {percent(item.average_return_percent)}
                  </td>
                  <td className={cn("py-3 pr-4 text-right font-mono", returnClass(item.median_return_percent))}>
                    {percent(item.median_return_percent)}
                  </td>
                  <td className={cn("py-3 text-right font-mono", returnClass(item.average_alpha_percent))}>
                    {percent(item.average_alpha_percent)}
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-muted-foreground">
                    No mature outcomes are available for this view.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

export default function RankingValidationPage() {
  const [horizon, setHorizon] = useState<RankingValidationHorizon>(1);
  const { data, isLoading, isError, error, refetch, isFetching } =
    useRankingValidation(horizon);

  if (isLoading) {
    return (
      <div className="max-w-[1550px] space-y-5 p-8">
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="max-w-[1200px] p-8">
        <Card className="border-rose-500/30">
          <CardContent className="flex items-start gap-3 p-6">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-rose-400" />
            <div>
              <p className="font-semibold">Ranking validation could not be loaded.</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error ? error.message : "Unknown API error."}
              </p>
              <Button className="mt-4" variant="outline" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const selected = data.selected_horizon;
  const topThree = data.rank_buckets.find((item) => item.code === "RANK_TOP_3");
  const others = data.rank_buckets.find((item) => item.code !== "RANK_TOP_3" && item.sample_count > 0);
  const ready = data.readiness_buckets.find((item) => item.code === "EXECUTION_READY");
  const blocked = data.readiness_buckets.find((item) => item.code === "EXECUTION_BLOCKED");

  return (
    <div className="max-w-[1550px] space-y-5 p-8">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary">
            <FlaskConical className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Ranking Validation</h1>
              <span className="rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#D4AF37]">
                v0.11
              </span>
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-sky-400">
                Advisory only
              </span>
            </div>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">
              Measures whether higher Opportunity Scores and stronger ranks produce better
              forward returns. Entry begins at the next trading-session open and results are
              compared with {data.benchmark_symbol}.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.available_horizons.map((value) => (
            <Button
              key={value}
              size="sm"
              variant={horizon === value ? "default" : "outline"}
              onClick={() => setHorizon(value)}
            >
              {value}D
            </Button>
          ))}
          <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={cn("mr-2 h-4 w-4", isFetching && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="Measured outcomes" value={String(selected.sample_count)} hint={`${horizon}D validation sample`} />
        <MetricCard label="Pending" value={String(selected.pending_count)} hint="Cohorts awaiting future sessions" />
        <MetricCard label="Hit rate" value={percent(selected.hit_rate_percent)} hint="Positive absolute return" />
        <MetricCard label="Average return" value={percent(selected.average_return_percent)} hint={`After ${horizon} trading day${horizon === 1 ? "" : "s"}`} />
        <MetricCard label="Average alpha" value={percent(selected.average_alpha_percent)} hint={`Relative to ${data.benchmark_symbol}`} />
        <MetricCard label="Score correlation" value={number(selected.score_return_correlation)} hint="Positive supports score ordering" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Target className="h-4 w-4 text-primary" />
              Does ranking add value?
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border bg-muted/20 p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Top three</p>
              <p className={cn("mt-2 font-mono text-2xl font-black", returnClass(topThree?.average_return_percent ?? null))}>
                {percent(topThree?.average_return_percent ?? null)}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {topThree?.sample_count ?? 0} measured cohort(s)
              </p>
            </div>
            <div className="rounded-lg border bg-muted/20 p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Lower-ranked comparison</p>
              <p className={cn("mt-2 font-mono text-2xl font-black", returnClass(others?.average_return_percent ?? null))}>
                {percent(others?.average_return_percent ?? null)}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {others?.sample_count ?? 0} measured cohort(s)
              </p>
            </div>
            <div className="rounded-lg border bg-muted/20 p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Execution ready</p>
              <p className={cn("mt-2 font-mono text-2xl font-black", returnClass(ready?.average_return_percent ?? null))}>
                {percent(ready?.average_return_percent ?? null)}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {ready?.sample_count ?? 0} measured cohort(s)
              </p>
            </div>
            <div className="rounded-lg border bg-muted/20 p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Execution blocked</p>
              <p className={cn("mt-2 font-mono text-2xl font-black", returnClass(blocked?.average_return_percent ?? null))}>
                {percent(blocked?.average_return_percent ?? null)}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {blocked?.sample_count ?? 0} measured cohort(s)
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Gauge className="h-4 w-4 text-primary" />
              Horizon maturity
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.horizons.map((item) => (
              <div key={item.horizon_days} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-base font-black">{item.label}</span>
                  <span className={cn("rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider", maturityClass(item.maturity))}>
                    {item.maturity}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-5 text-right text-xs">
                  <div>
                    <p className="text-muted-foreground">Sample</p>
                    <p className="font-mono font-bold">{item.sample_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Hit rate</p>
                    <p className="font-mono font-bold">{percent(item.hit_rate_percent)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Avg return</p>
                    <p className={cn("font-mono font-bold", returnClass(item.average_return_percent))}>
                      {percent(item.average_return_percent)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <BucketTable title="Score-band calibration" icon={TrendingUp} items={data.score_bands} />
        <BucketTable title="Return by original rank" icon={Scale} items={data.rank_buckets} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <BucketTable title="Symbol performance" icon={BarChart3} items={data.symbol_performance} />
        <BucketTable title="Sector performance" icon={BarChart3} items={data.sector_performance} />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Clock3 className="h-4 w-4 text-primary" />
            Latest measured outcomes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-xs">
              <thead className="border-b text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="pb-2 pr-4">Symbol</th>
                  <th className="pb-2 pr-4 text-right">Original rank</th>
                  <th className="pb-2 pr-4 text-right">Score</th>
                  <th className="pb-2 pr-4 text-right">Return</th>
                  <th className="pb-2 pr-4 text-right">Alpha</th>
                  <th className="pb-2 pr-4 text-right">Drawdown</th>
                  <th className="pb-2 pr-4">Entry → Exit</th>
                  <th className="pb-2">Readiness</th>
                </tr>
              </thead>
              <tbody>
                {data.latest_outcomes.map((item) => {
                  const PositiveIcon = item.return_percent >= 0 ? ArrowUpRight : ArrowDownRight;
                  return (
                    <tr key={item.outcome_id} className="border-b border-border/60 last:border-0">
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <PositiveIcon className={cn("h-3.5 w-3.5", returnClass(item.return_percent))} />
                          <span className="font-mono font-black text-primary">{item.symbol}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-right font-mono">#{item.original_rank}</td>
                      <td className="py-3 pr-4 text-right font-mono">{item.opportunity_score.toFixed(1)}</td>
                      <td className={cn("py-3 pr-4 text-right font-mono font-bold", returnClass(item.return_percent))}>
                        {percent(item.return_percent)}
                      </td>
                      <td className={cn("py-3 pr-4 text-right font-mono", returnClass(item.alpha_percent))}>
                        {percent(item.alpha_percent)}
                      </td>
                      <td className="py-3 pr-4 text-right font-mono text-rose-300">
                        {percent(item.maximum_drawdown_percent)}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {item.entry_date} → {item.exit_date}
                      </td>
                      <td className="py-3">
                        <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider", item.eligible_for_execution ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : "border-amber-500/30 bg-amber-500/10 text-amber-400")}>
                          {item.eligible_for_execution ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                          {item.eligible_for_execution ? "Ready" : "Blocked"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
                {data.latest_outcomes.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-10 text-center text-muted-foreground">
                      No {horizon}D outcomes have matured yet. KAIRO will measure them automatically after future trading sessions become available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {data.warnings.length > 0 && (
        <Card className="border-amber-500/25">
          <CardContent className="space-y-2 p-4">
            {data.warnings.map((warning) => (
              <div key={warning} className="flex items-start gap-2 text-xs leading-5 text-amber-200">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{warning}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
