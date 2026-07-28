import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  CircleDot,
  Clock3,
  Gauge,
  History,
  ListOrdered,
  MessageSquareText,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  OpportunityHistoryOverviewReport,
  OpportunityRankingComponent,
  OpportunitySymbolHistoryReport,
  RankedOpportunity,
  useOpportunityRanking,
  useOpportunityRankingHistory,
  useOpportunityRankingHistoryOverview,
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

function signed(value: number, digits = 1): string {
  if (Math.abs(value) < 0.005) return "0.0";
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function scoreClass(score: number): string {
  if (score >= 75) return "text-emerald-400";
  if (score >= 60) return "text-[#D4AF37]";
  if (score >= 45) return "text-sky-400";
  return "text-muted-foreground";
}

function movementClass(value: number): string {
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-destructive";
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

function MovementOverview({
  data,
  isLoading,
}: {
  data: OpportunityHistoryOverviewReport | undefined;
  isLoading: boolean;
}) {
  if (isLoading) return <Skeleton className="h-36 w-full" />;
  if (!data || data.tracked_symbol_count === 0) {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 p-4 text-sm text-muted-foreground">
          <History className="h-4 w-4" />
          Rank history will populate after the next Intelligence Cycle.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <TrendingUp className="h-4 w-4 text-primary" />
          24-hour rank drift
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
            Largest risers
          </p>
          <div className="space-y-2">
            {data.largest_risers.length ? data.largest_risers.map((item) => (
              <div key={item.symbol} className="flex items-center justify-between rounded-md border p-2 text-sm">
                <span className="font-mono font-bold">{item.symbol}</span>
                <span className="flex items-center gap-2 text-emerald-400">
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  {signed(item.score_change)} pts · {item.rank_change > 0 ? `+${item.rank_change}` : item.rank_change} rank
                </span>
              </div>
            )) : <p className="text-xs text-muted-foreground">No improving scores yet.</p>}
          </div>
        </div>
        <div>
          <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
            Largest fallers
          </p>
          <div className="space-y-2">
            {data.largest_fallers.length ? data.largest_fallers.map((item) => (
              <div key={item.symbol} className="flex items-center justify-between rounded-md border p-2 text-sm">
                <span className="font-mono font-bold">{item.symbol}</span>
                <span className="flex items-center gap-2 text-destructive">
                  <ArrowDownRight className="h-3.5 w-3.5" />
                  {signed(item.score_change)} pts · {item.rank_change} rank
                </span>
              </div>
            )) : <p className="text-xs text-muted-foreground">No weakening scores yet.</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RankDriftPanel({
  data,
  isLoading,
  windowDays,
  onWindowChange,
}: {
  data: OpportunitySymbolHistoryReport | undefined;
  isLoading: boolean;
  windowDays: 1 | 7 | 30;
  onWindowChange: (value: 1 | 7 | 30) => void;
}) {
  const chartData = useMemo(
    () => (data?.snapshots ?? []).map((snapshot) => ({
      captured_at: snapshot.captured_at,
      label: new Date(snapshot.captured_at).toLocaleString(),
      score: snapshot.opportunity_score,
      rank: snapshot.rank,
    })),
    [data],
  );

  return (
    <Card data-testid="rank-drift-panel">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <History className="h-4 w-4 text-primary" />
            Opportunity History &amp; Rank Drift
          </CardTitle>
          <div className="flex gap-1">
            {([1, 7, 30] as const).map((value) => (
              <Button
                key={value}
                size="sm"
                variant={windowDays === value ? "default" : "outline"}
                onClick={() => onWindowChange(value)}
              >
                {value === 1 ? "24h" : `${value}d`}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : !data || data.snapshot_count === 0 ? (
          <div className="flex h-44 flex-col items-center justify-center gap-2 text-center text-sm text-muted-foreground">
            <Clock3 className="h-6 w-6" />
            History will populate after KAIRO captures this opportunity in an Intelligence Cycle.
          </div>
        ) : (
          <div className="space-y-5">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg border p-3">
                <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Score movement</p>
                <p className={cn("mt-1 font-mono text-xl font-bold", movementClass(data.score_change))}>
                  {signed(data.score_change)} pts
                </p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Rank movement</p>
                <p className={cn("mt-1 font-mono text-xl font-bold", movementClass(data.rank_change))}>
                  {data.rank_change > 0 ? `Up ${data.rank_change}` : data.rank_change < 0 ? `Down ${Math.abs(data.rank_change)}` : "Unchanged"}
                </p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Current streak</p>
                <p className="mt-1 text-sm font-bold">{displayName(data.streak_direction)}</p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Observed history</p>
                <p className="mt-1 text-sm font-bold">{data.snapshot_count} meaningful snapshots</p>
                <p className="text-[10px] text-muted-foreground">
                  First seen {data.first_seen_at ? new Date(data.first_seen_at).toLocaleString() : "—"}
                </p>
              </div>
            </div>

            {chartData.length > 1 ? (
              <div className="h-72 rounded-lg border p-3">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.18} />
                    <XAxis dataKey="captured_at" tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} />
                    <YAxis yAxisId="score" domain={[0, 100]} />
                    <YAxis yAxisId="rank" orientation="right" reversed allowDecimals={false} domain={[1, "dataMax + 1"]} />
                    <Tooltip labelFormatter={(value) => new Date(String(value)).toLocaleString()} />
                    <Line yAxisId="score" type="monotone" dataKey="score" name="Opportunity score" stroke="var(--color-primary)" strokeWidth={2} dot />
                    <Line yAxisId="rank" type="stepAfter" dataKey="rank" name="Rank" stroke="var(--color-chart-2)" strokeWidth={2} dot />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="rounded-lg border p-4 text-sm text-muted-foreground">
                A second meaningful snapshot is required before KAIRO can draw the drift chart.
              </div>
            )}

            <div>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
                Meaningful change timeline
              </p>
              {data.changes.length ? (
                <div className="space-y-3">
                  {[...data.changes].reverse().slice(0, 8).map((change) => (
                    <div key={`${change.captured_at}-${change.summary}`} className="rounded-lg border p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-sm font-semibold">{change.summary}</p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {new Date(change.captured_at).toLocaleString()}
                          </p>
                        </div>
                        <span className={cn("text-xs font-bold", movementClass(change.score_change))}>
                          {signed(change.score_change)} score · {change.rank_change > 0 ? `+${change.rank_change}` : change.rank_change} rank
                        </span>
                      </div>
                      {change.component_changes.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {change.component_changes.map((component) => (
                            <span key={component.code} className="rounded-full border px-2 py-1 text-[10px] text-muted-foreground">
                              {component.label} {signed(component.change)}
                            </span>
                          ))}
                        </div>
                      )}
                      {(change.blockers_added.length > 0 || change.blockers_resolved.length > 0) && (
                        <div className="mt-3 space-y-1 text-xs">
                          {change.blockers_added.map((blocker) => <p key={`added-${blocker}`} className="text-amber-400">Blocker added: {blocker}</p>)}
                          {change.blockers_resolved.map((blocker) => <p key={`resolved-${blocker}`} className="text-emerald-400">Blocker resolved: {blocker}</p>)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No meaningful movement has been recorded in this window.</p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SelectedOpportunity({
  item,
  history,
  historyLoading,
  historyWindow,
  onHistoryWindowChange,
}: {
  item: RankedOpportunity;
  history: OpportunitySymbolHistoryReport | undefined;
  historyLoading: boolean;
  historyWindow: 1 | 7 | 30;
  onHistoryWindowChange: (value: 1 | 7 | 30) => void;
}) {
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
                <span className={cn("rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider", categoryClass(item.category))}>
                  {displayName(item.category)}
                </span>
              </div>
              <h2 className="mt-3 max-w-3xl text-lg font-semibold">{item.headline}</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {displayName(item.recommendation)} · {item.sector} · {displayName(item.risk_tier)} risk
              </p>
            </div>
            <div className="rounded-xl border border-primary/25 bg-background/80 px-5 py-4 text-right">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">Opportunity score</p>
              <p className={cn("mt-1 font-mono text-4xl font-black", scoreClass(item.opportunity_score))}>{item.opportunity_score.toFixed(1)}</p>
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
            <p className="mt-1 font-mono text-xl font-bold">{item.expected_return_percent == null ? "—" : `${item.expected_return_percent.toFixed(2)}%`}</p>
            <p className="text-[10px] text-muted-foreground">Measured samples only</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Evidence coverage</p>
            <p className="mt-1 font-mono text-xl font-bold">{item.evidence_coverage_percent.toFixed(1)}%</p>
            <p className="text-[10px] text-muted-foreground">{displayName(item.data_quality)} quality</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Execution state</p>
            <p className={cn("mt-1 text-sm font-bold", item.eligible_for_execution ? "text-emerald-400" : "text-amber-400")}>
              {item.eligible_for_execution ? "READY" : "BLOCKED"}
            </p>
            <p className="text-[10px] text-muted-foreground">{item.blockers.length} active blocker(s)</p>
          </div>
        </CardContent>
      </Card>

      <RankDriftPanel data={history} isLoading={historyLoading} windowDays={historyWindow} onWindowChange={onHistoryWindowChange} />

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
                  <p className="font-mono text-sm font-bold">{component.value.toFixed(1)} / {component.maximum.toFixed(1)}</p>
                  <p className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground">{displayName(component.status)}</p>
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
            <p className="mt-1 text-xs text-muted-foreground">Ranking is advisory and never bypasses KAIRO&apos;s execution, graduation or risk gates.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/decision-explainability">
              <Button variant="outline"><BarChart3 className="mr-2 h-4 w-4" />Decision evidence</Button>
            </Link>
            <Link href={`/copilot?question=${copilotQuestion}`}>
              <Button><MessageSquareText className="mr-2 h-4 w-4" />Ask Copilot</Button>
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
  const [historyWindow, setHistoryWindow] = useState<1 | 7 | 30>(7);

  useEffect(() => {
    if (!selectedSymbol && data?.items.length) setSelectedSymbol(data.items[0].symbol);
  }, [data, selectedSymbol]);

  const selected = useMemo(
    () => data?.items.find((item) => item.symbol === selectedSymbol) ?? data?.items[0],
    [data, selectedSymbol],
  );

  const historyQuery = useOpportunityRankingHistory(selected?.symbol ?? "", historyWindow);
  const overviewQuery = useOpportunityRankingHistoryOverview(1);

  if (isLoading) {
    return (
      <div className="space-y-5 p-8">
        <Skeleton className="h-20 w-full" />
        <div className="grid gap-5 xl:grid-cols-[340px_minmax(0,1fr)]"><Skeleton className="h-[520px]" /><Skeleton className="h-[620px]" /></div>
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
              <p className="mt-1 text-sm text-muted-foreground">{error instanceof Error ? error.message : "The ranking report could not be loaded."}</p>
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
          <div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary"><Target className="h-6 w-6" /></div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Opportunity Ranking</h1>
              <span className="rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#D4AF37]">v0.10</span>
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-sky-400">Advisory only</span>
            </div>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">{data.methodology_summary} Rankings never weaken existing risk, execution or graduation controls.</p>
          </div>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={cn("mr-2 h-4 w-4", isFetching && "animate-spin")} />Refresh ranking
        </Button>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Ranked opportunities" value={String(data.ranking_count)} hint="Current intelligence shortlist" />
        <MetricCard label="Execution ready" value={String(data.execution_ready_count)} hint="All gates currently passed" />
        <MetricCard label="High potential blocked" value={String(data.high_potential_blocked_count)} hint="Strong score with active gates" />
        <MetricCard label="Market data" value={displayName(data.market_data_status)} hint={`${data.performance_window_days}-day performance window`} />
      </div>

      <MovementOverview data={overviewQuery.data} isLoading={overviewQuery.isLoading} />

      {data.warnings.length > 0 && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-400" />
            <div className="space-y-1 text-sm">{data.warnings.slice(0, 4).map((warning) => <p key={warning}>{warning}</p>)}</div>
          </CardContent>
        </Card>
      )}

      {data.items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-12 text-center">
            <Sparkles className="h-8 w-8 text-muted-foreground" />
            <p className="font-semibold">No current opportunities are available</p>
            <p className="max-w-xl text-sm text-muted-foreground">Run an Intelligence Cycle to produce a ranked opportunity shortlist.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid items-start gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
          <RankingList items={data.items} selectedSymbol={selected?.symbol ?? ""} onSelect={setSelectedSymbol} />
          {selected && (
            <SelectedOpportunity
              item={selected}
              history={historyQuery.data}
              historyLoading={historyQuery.isLoading}
              historyWindow={historyWindow}
              onHistoryWindowChange={setHistoryWindow}
            />
          )}
        </div>
      )}

      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>{data.methodology_version}</span>
        <span className="flex items-center gap-1"><TrendingUp className="h-3 w-3" />Generated {new Date(data.generated_at).toLocaleString()}</span>
      </div>
    </div>
  );
}
