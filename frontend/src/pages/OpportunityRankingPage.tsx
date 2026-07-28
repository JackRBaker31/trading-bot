import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  CircleDot,
  Gauge,
  ListOrdered,
  MessageSquareText,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  OpportunityRankingComponent,
  RankedOpportunity,
  useOpportunityRanking,
} from "@/hooks/useOpportunityRanking";
import { cn } from "@/lib/utils";

function displayName(value: string | null | undefined): string {
  if (!value) return "Not available";
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function percentage(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value <= 1 ? value * 100 : value).toFixed(1)}%`;
}

function scoreClass(score: number): string {
  if (score >= 75) return "text-emerald-400";
  if (score >= 60) return "text-[#D4AF37]";
  if (score >= 45) return "text-sky-400";
  return "text-muted-foreground";
}

function categoryClass(category: string): string {
  if (category === "PRIORITY_READY") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  }
  if (category === "HIGH_POTENTIAL_BLOCKED") {
    return "border-amber-500/30 bg-amber-500/10 text-amber-400";
  }
  if (category === "PROMISING_IMMATURE") {
    return "border-sky-500/30 bg-sky-500/10 text-sky-400";
  }
  if (category === "INSUFFICIENT_DATA") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  return "border-border bg-muted/40 text-muted-foreground";
}

function componentPercent(component: OpportunityRankingComponent): number {
  if (component.maximum <= 0) return 0;
  return Math.max(0, Math.min(100, (component.value / component.maximum) * 100));
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

function RankingList({
  items,
  selectedSymbol,
  onSelect,
}: {
  items: RankedOpportunity[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}) {
  return (
    <Card className="h-fit">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <ListOrdered className="h-4 w-4 text-primary" />
          Current ranking
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.map((item) => {
          const selected = selectedSymbol === item.symbol;
          return (
            <button
              key={item.symbol}
              type="button"
              data-testid={`ranking-symbol-${item.symbol}`}
              onClick={() => onSelect(item.symbol)}
              className={cn(
                "w-full rounded-lg border p-3 text-left transition-colors",
                selected
                  ? "border-primary/50 bg-primary/10"
                  : "border-border bg-background hover:border-primary/25 hover:bg-muted/30",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground">#{item.rank}</span>
                    <span className="font-mono text-base font-black text-primary">{item.symbol}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                    {item.headline}
                  </p>
                </div>
                <div className="text-right">
                  <p className={cn("font-mono text-xl font-black", scoreClass(item.opportunity_score))}>
                    {item.opportunity_score.toFixed(1)}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    {percentage(item.calibrated_confidence)}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <span
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                    categoryClass(item.category),
                  )}
                >
                  {displayName(item.category)}
                </span>
                <span className="rounded-full border border-border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-muted-foreground">
                  {item.eligible_for_execution ? "Ready" : "Blocked"}
                </span>
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}

function EvidenceCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "warning" | "neutral";
}) {
  const Icon = tone === "positive" ? CheckCircle2 : tone === "warning" ? AlertTriangle : CircleDot;
  const iconClass = tone === "positive" ? "text-emerald-400" : tone === "warning" ? "text-amber-400" : "text-primary";

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length > 0 ? (
          <div className="space-y-3">
            {items.map((item, index) => (
              <div key={`${item}-${index}`} className="flex items-start gap-2 text-sm leading-6">
                <Icon className={cn("mt-1 h-3.5 w-3.5 shrink-0", iconClass)} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No recorded items.</p>
        )}
      </CardContent>
    </Card>
  );
}

function SelectedOpportunity({ item }: { item: RankedOpportunity }) {
  const copilotQuestion = encodeURIComponent(
    `Explain why ${item.symbol} is ranked #${item.rank} with an opportunity score of ${item.opportunity_score.toFixed(1)} and what would improve it.`,
  );

  return (
    <div className="space-y-5">
      <Card className="overflow-hidden">
        <div className="border-b border-border bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.10),transparent_48%)] p-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold text-muted-foreground">#{item.rank}</span>
                <span className="font-mono text-3xl font-black text-primary">{item.symbol}</span>
                <span
                  className={cn(
                    "rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
                    categoryClass(item.category),
                  )}
                >
                  {displayName(item.category)}
                </span>
              </div>
              <h2 className="mt-3 max-w-3xl text-lg font-semibold">{item.headline}</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {displayName(item.recommendation)} · {item.sector} · {displayName(item.risk_tier)} risk
              </p>
            </div>
            <div className="rounded-xl border border-primary/25 bg-background/80 px-5 py-4 text-right">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
                Opportunity score
              </p>
              <p className={cn("mt-1 font-mono text-4xl font-black", scoreClass(item.opportunity_score))}>
                {item.opportunity_score.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">out of 100</p>
            </div>
          </div>
        </div>
        <CardContent className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg border p-3">
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Calibrated confidence</p>
            <p className="mt-1 font-mono text-xl font-bold">{percentage(item.calibrated_confidence)}</p>
            <p className="text-[10px] text-muted-foreground">{item.confidence_sample_count} measured band cases</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Expected return</p>
            <p className="mt-1 font-mono text-xl font-bold">
              {item.expected_return_percent == null ? "—" : `${item.expected_return_percent.toFixed(2)}%`}
            </p>
            <p className="text-[10px] text-muted-foreground">Measured samples only</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Evidence coverage</p>
            <p className="mt-1 font-mono text-xl font-bold">{item.evidence_coverage_percent.toFixed(1)}%</p>
            <p className="text-[10px] text-muted-foreground">{displayName(item.data_quality)} quality</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Execution state</p>
            <p className={cn("mt-1 text-sm font-bold", item.eligible_for_execution ? "text-emerald-400" : "text-amber-400") }>
              {item.eligible_for_execution ? "READY" : "BLOCKED"}
            </p>
            <p className="text-[10px] text-muted-foreground">{item.blockers.length} active blocker(s)</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Gauge className="h-4 w-4 text-primary" />
            Score composition
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 xl:grid-cols-2">
          {item.components.map((component) => (
            <div key={component.code} className="rounded-lg border border-border p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold">{component.label}</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{component.detail}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm font-bold">
                    {component.value.toFixed(1)} / {component.maximum.toFixed(1)}
                  </p>
                  <p className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground">
                    {displayName(component.status)}
                  </p>
                </div>
              </div>
              <Progress value={componentPercent(component)} className="mt-4 h-2" />
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-3">
        <EvidenceCard title="Positive contributors" items={item.positive_contributors} tone="positive" />
        <EvidenceCard title="Penalties and constraints" items={item.penalties} tone="warning" />
        <EvidenceCard title="What would improve the rank" items={item.improvement_actions} tone="neutral" />
      </div>

      <Card>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold">Continue the investigation</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Ranking is advisory and never bypasses KAIRO&apos;s execution, graduation or risk gates.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/decision-explainability">
              <Button variant="outline">
                <BarChart3 className="mr-2 h-4 w-4" />
                Decision evidence
              </Button>
            </Link>
            <Link href={`/copilot?question=${copilotQuestion}`}>
              <Button>
                <MessageSquareText className="mr-2 h-4 w-4" />
                Ask Copilot
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function OpportunityRankingPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useOpportunityRanking();
  const [selectedSymbol, setSelectedSymbol] = useState("");

  useEffect(() => {
    if (!selectedSymbol && data?.items.length) {
      setSelectedSymbol(data.items[0].symbol);
    }
  }, [data, selectedSymbol]);

  const selected = useMemo(
    () => data?.items.find((item) => item.symbol === selectedSymbol) ?? data?.items[0],
    [data, selectedSymbol],
  );

  if (isLoading) {
    return (
      <div className="space-y-5 p-8">
        <Skeleton className="h-20 w-full" />
        <div className="grid gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
          <Skeleton className="h-[520px]" />
          <Skeleton className="h-[620px]" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-8">
        <Card className="border-destructive/30">
          <CardContent className="flex items-start gap-3 p-5">
            <ShieldAlert className="mt-0.5 h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Opportunity Ranking is unavailable</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error ? error.message : "The ranking report could not be loaded."}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-[1550px] space-y-5 p-8">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary">
            <Target className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Opportunity Ranking</h1>
              <span className="rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#D4AF37]">
                v0.9
              </span>
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-sky-400">
                Advisory only
              </span>
            </div>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">
              {data.methodology_summary} Rankings never weaken existing risk, execution or graduation controls.
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={cn("mr-2 h-4 w-4", isFetching && "animate-spin")} />
          Refresh ranking
        </Button>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Ranked opportunities" value={String(data.ranking_count)} hint="Current intelligence shortlist" />
        <MetricCard label="Execution ready" value={String(data.execution_ready_count)} hint="All gates currently passed" />
        <MetricCard label="High potential blocked" value={String(data.high_potential_blocked_count)} hint="Strong score with active gates" />
        <MetricCard label="Market data" value={displayName(data.market_data_status)} hint={`${data.performance_window_days}-day performance window`} />
      </div>

      {data.warnings.length > 0 && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-400" />
            <div className="space-y-1 text-sm">
              {data.warnings.slice(0, 4).map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {data.items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-12 text-center">
            <Sparkles className="h-8 w-8 text-muted-foreground" />
            <p className="font-semibold">No current opportunities are available</p>
            <p className="max-w-xl text-sm text-muted-foreground">
              Run an Intelligence Cycle to produce a ranked opportunity shortlist.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid items-start gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
          <RankingList items={data.items} selectedSymbol={selected?.symbol ?? ""} onSelect={setSelectedSymbol} />
          {selected && <SelectedOpportunity item={selected} />}
        </div>
      )}

      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>{data.methodology_version}</span>
        <span className="flex items-center gap-1">
          <TrendingUp className="h-3 w-3" />
          Generated {new Date(data.generated_at).toLocaleString()}
        </span>
      </div>
    </div>
  );
}
