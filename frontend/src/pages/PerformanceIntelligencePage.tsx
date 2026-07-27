import { useMemo, useState } from "react";
import {
  Activity, AlertTriangle, BarChart3, Brain, CheckCircle2, Clock3,
  Download, FileText, Gauge, Layers3, Newspaper, RefreshCw,
  ShieldCheck, Target, TrendingUp, XCircle,
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReviewPreset, usePerformanceReview } from "@/hooks/usePerformanceReview";
import { cn } from "@/lib/utils";

const presets: Array<{ value: ReviewPreset; label: string }> = [
  { value: "24h", label: "Last 24 Hours" },
  { value: "weekend", label: "Weekend Review" },
  { value: "7d", label: "Last 7 Days" },
  { value: "30d", label: "Last 30 Days" },
];

function MetricCard({ title, value, detail, icon: Icon }: { title: string; value: string; detail: string; icon: typeof Activity }) {
  return <Card className="border-border/70 bg-card/70"><CardContent className="p-5"><div className="mb-4 flex items-center justify-between"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{title}</p><Icon className="h-4 w-4 text-primary" /></div><p className="text-3xl font-semibold tracking-tight">{value}</p><p className="mt-2 text-xs text-muted-foreground">{detail}</p></CardContent></Card>;
}

function EmptyChart({ message }: { message: string }) {
  return <div className="flex h-72 items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">{message}</div>;
}

function downloadMarkdown(markdown: string) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `kairo-performance-review-${new Date().toISOString().slice(0, 10)}.md`;
  link.click();
  URL.revokeObjectURL(url);
}

function shortDate(value: string) {
  return new Date(`${value}T00:00:00Z`).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function PerformanceIntelligencePage() {
  const [preset, setPreset] = useState<ReviewPreset>("weekend");
  const review = usePerformanceReview(preset);

  const maturityComponents = useMemo(
    () =>
      Object.entries(review.data?.maturity?.components ?? {}).map(
        ([name, value]) => ({
          name: name.replaceAll("_", " "),
          value,
        }),
      ),
    [review.data?.maturity?.components],
  );

  if (review.isLoading) return <div className="space-y-4"><Skeleton className="h-20 w-full" /><div className="grid gap-4 md:grid-cols-4">{Array.from({ length: 8 }).map((_, index) => <Skeleton key={index} className="h-36" />)}</div></div>;
  if (!review.data) return <Card><CardContent className="p-8 text-center"><AlertTriangle className="mx-auto mb-3 h-8 w-8 text-amber-400" /><p className="font-semibold">Performance review unavailable</p><p className="mt-1 text-sm text-muted-foreground">{review.error instanceof Error ? review.error.message : "The review could not be generated."}</p></CardContent></Card>;

  const data = review.data;
  const health = data.system_health;
  const research = data.research_activity;
  const decisions = data.decision_intelligence;
  const performance = data.shadow_performance;
  const confidence = data.confidence_calibration;
  const calibratedBuckets = (confidence.calibration_buckets ?? []).filter(item => item.decision_count > 0);
  const sectorRows = (data.sector_analytics ?? []).slice(0, 10);
  const symbolRows = (data.symbol_analytics ?? []).slice(0, 15);

  return <div className="space-y-6">
    <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary"><BarChart3 className="h-4 w-4" />KAIRO Analytics 2.0</div><h1 className="text-3xl font-semibold tracking-tight">Performance Intelligence</h1><p className="mt-2 max-w-3xl text-sm text-muted-foreground">Understand reliability, research efficiency, confidence calibration, sector performance and the decisions KAIRO is learning from.</p></div>
      <div className="flex flex-wrap gap-2">{presets.map(item => <Button key={item.value} size="sm" variant={preset === item.value ? "default" : "outline"} onClick={() => setPreset(item.value)}>{item.label}</Button>)}<Button size="sm" variant="outline" onClick={() => review.refetch()}><RefreshCw className={cn("mr-2 h-4 w-4", review.isFetching && "animate-spin")} />Refresh</Button><Button size="sm" variant="outline" onClick={() => downloadMarkdown(data.markdown)}><Download className="mr-2 h-4 w-4" />Export</Button></div>
    </div>

    <Card className="border-primary/20 bg-gradient-to-br from-primary/[0.10] via-card to-card"><CardContent className="grid gap-6 p-6 xl:grid-cols-[1fr_260px]"><div><div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary"><FileText className="h-4 w-4" />Executive Review</div><p className="max-w-5xl text-base leading-7">{data.executive_summary}</p><p className="mt-4 text-xs text-muted-foreground">{new Date(data.period.start).toLocaleString()} — {new Date(data.period.end).toLocaleString()} · {data.period.hours.toFixed(1)} hours</p></div><div className="rounded-lg border bg-background/45 p-4"><div className="flex items-center justify-between"><span className="text-xs uppercase tracking-wider text-muted-foreground">Platform maturity</span><Gauge className="h-4 w-4 text-primary" /></div><div className="mt-3 flex items-end justify-between"><span className="text-4xl font-semibold">{data.maturity.score_percent}%</span><span className="text-sm font-medium text-primary">{data.maturity.label}</span></div><Progress className="mt-4" value={data.maturity.score_percent} /><p className="mt-3 text-xs text-muted-foreground">Graduation {data.maturity.graduation_passed_checks}/{data.maturity.graduation_total_checks} · {data.maturity.trading_readiness}</p></div></CardContent></Card>

    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricCard title="Healthy Completion" value={`${health.healthy_completion_percent}%`} detail={`${health.intelligence_cycles} intelligence cycles`} icon={ShieldCheck} /><MetricCard title="Research Created" value={research.created_count.toLocaleString()} detail={`${research.skipped_count.toLocaleString()} skipped · ${research.failure_count} failed`} icon={Newspaper} /><MetricCard title="Shadow Decisions" value={decisions.shadow_decisions.toLocaleString()} detail={`${decisions.eligible_decisions} eligible · ${decisions.average_confidence_percent}% avg confidence`} icon={Brain} /><MetricCard title="Measured Accuracy" value={`${performance.directional_success_percent}%`} detail={`${performance.measured_1d_decisions} measured 1-day decisions`} icon={Target} /></div>

    <Tabs defaultValue="overview" className="space-y-4">
      <TabsList className="h-auto flex-wrap"><TabsTrigger value="overview">Overview</TabsTrigger><TabsTrigger value="calibration">Confidence</TabsTrigger><TabsTrigger value="sectors">Sectors</TabsTrigger><TabsTrigger value="symbols">Symbols</TabsTrigger><TabsTrigger value="blockers">Blockers</TabsTrigger></TabsList>

      <TabsContent value="overview" className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-2">
          <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-4 w-4 text-primary" />Operational trend</CardTitle></CardHeader><CardContent>{data.trends.length ? <ResponsiveContainer width="100%" height={300}><AreaChart data={data.trends}><CartesianGrid strokeDasharray="3 3" opacity={0.18} /><XAxis dataKey="date" tickFormatter={shortDate} /><YAxis allowDecimals={false} /><Tooltip labelFormatter={shortDate} /><Area type="monotone" dataKey="healthy_cycles" name="Healthy cycles" stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.18} /><Line type="monotone" dataKey="failed_cycles" name="Failed cycles" stroke="var(--color-destructive)" /></AreaChart></ResponsiveContainer> : <EmptyChart message="No operational trend data in this period." />}</CardContent></Card>
          <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><TrendingUp className="h-4 w-4 text-primary" />Research and decisions</CardTitle></CardHeader><CardContent>{data.trends.length ? <ResponsiveContainer width="100%" height={300}><LineChart data={data.trends}><CartesianGrid strokeDasharray="3 3" opacity={0.18} /><XAxis dataKey="date" tickFormatter={shortDate} /><YAxis allowDecimals={false} /><Tooltip labelFormatter={shortDate} /><Line type="monotone" dataKey="created" name="Research created" stroke="var(--color-primary)" strokeWidth={2} /><Line type="monotone" dataKey="decisions" name="Shadow decisions" stroke="var(--color-chart-2)" strokeWidth={2} /></LineChart></ResponsiveContainer> : <EmptyChart message="No research trend data in this period." />}</CardContent></Card>
        </div>
        <div className="grid gap-4 xl:grid-cols-3">
          <Card><CardHeader><CardTitle className="text-base">System health</CardTitle></CardHeader><CardContent className="space-y-4"><div><div className="mb-2 flex justify-between text-sm"><span>Healthy jobs</span><span>{health.healthy_completion_percent}%</span></div><Progress value={health.healthy_completion_percent} /></div><div className="grid grid-cols-2 gap-3"><div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Succeeded</p><p className="mt-1 text-xl font-semibold text-emerald-400">{health.succeeded}</p></div><div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Warnings</p><p className="mt-1 text-xl font-semibold text-amber-400">{health.succeeded_with_warnings}</p></div><div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Failed</p><p className="mt-1 text-xl font-semibold text-red-400">{health.failed}</p></div><div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Abandoned</p><p className="mt-1 text-xl font-semibold">{health.abandoned_running}</p></div></div><div className="flex justify-between rounded-md border p-3 text-sm"><span>Average cycle</span><strong>{health.average_cycle_duration_seconds}s</strong></div></CardContent></Card>
          <Card><CardHeader><CardTitle className="text-base">Growth components</CardTitle></CardHeader><CardContent className="space-y-4">{maturityComponents.map(item => <div key={item.name}><div className="mb-1 flex justify-between text-sm capitalize"><span>{item.name}</span><strong>{item.value}/25</strong></div><Progress value={item.value * 4} /></div>)}</CardContent></Card>
          <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><CheckCircle2 className="h-4 w-4 text-primary" />Insights</CardTitle></CardHeader><CardContent className="space-y-3">{data.insights.map((insight, index) => <div key={index} className="flex gap-3 rounded-md border bg-muted/20 p-3 text-sm leading-6"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" /><span>{insight}</span></div>)}</CardContent></Card>
        </div>
      </TabsContent>

      <TabsContent value="calibration" className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-[2fr_1fr]"><Card><CardHeader><CardTitle className="text-base">Expected confidence vs measured accuracy</CardTitle></CardHeader><CardContent>{calibratedBuckets.length ? <ResponsiveContainer width="100%" height={340}><BarChart data={calibratedBuckets}><CartesianGrid strokeDasharray="3 3" opacity={0.18} /><XAxis dataKey="label" /><YAxis domain={[0, 100]} unit="%" /><Tooltip /><Bar dataKey="expected_accuracy_percent" name="Expected" fill="var(--color-primary)" radius={[4,4,0,0]} /><Bar dataKey="actual_accuracy_percent" name="Measured" fill="var(--color-chart-2)" radius={[4,4,0,0]} /></BarChart></ResponsiveContainer> : <EmptyChart message="Confidence buckets will populate as decision outcomes mature." />}</CardContent></Card><Card><CardHeader><CardTitle className="text-base">Calibration status</CardTitle></CardHeader><CardContent className="space-y-4"><div className="rounded-md border p-4"><p className="text-xs uppercase tracking-wider text-muted-foreground">Measured sample</p><p className="mt-2 text-3xl font-semibold">{confidence.calibration_sample_size}</p></div><div className="flex justify-between text-sm"><span>Latest snapshot</span><strong>{confidence.latest_snapshot_confidence_percent}%</strong></div><div className="flex justify-between text-sm"><span>Observed direction</span><strong>{performance.directional_success_percent}%</strong></div><div className="flex justify-between text-sm"><span>Mean calibration gap</span><strong>{confidence.mean_absolute_calibration_gap_points} pts</strong></div><div className="flex justify-between text-sm"><span>Stale snapshots</span><strong>{confidence.stale_snapshot_percent}%</strong></div></CardContent></Card></div>
      </TabsContent>

      <TabsContent value="sectors" className="space-y-4"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Layers3 className="h-4 w-4 text-primary" />Sector intelligence</CardTitle></CardHeader><CardContent>{sectorRows.length ? <ResponsiveContainer width="100%" height={380}><BarChart data={sectorRows} layout="vertical" margin={{ left: 24 }}><CartesianGrid strokeDasharray="3 3" opacity={0.18} /><XAxis type="number" domain={[0, 100]} unit="%" /><YAxis type="category" dataKey="sector" width={130} /><Tooltip /><Bar dataKey="average_confidence_percent" name="Average confidence" fill="var(--color-primary)" radius={[0,4,4,0]} /><Bar dataKey="directional_accuracy_percent" name="Measured accuracy" fill="var(--color-chart-2)" radius={[0,4,4,0]} /></BarChart></ResponsiveContainer> : <EmptyChart message="Sector analytics will appear after shadow decisions are created." />}</CardContent></Card><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{sectorRows.map(item => <Card key={item.sector}><CardContent className="p-4"><div className="flex items-center justify-between"><strong>{item.sector}</strong><span className="text-xs text-muted-foreground">{item.decision_count} decisions</span></div><div className="mt-4 grid grid-cols-3 gap-2 text-xs"><div><p className="text-muted-foreground">Confidence</p><p className="mt-1 font-semibold">{item.average_confidence_percent}%</p></div><div><p className="text-muted-foreground">Accuracy</p><p className="mt-1 font-semibold">{item.directional_accuracy_percent}%</p></div><div><p className="text-muted-foreground">Measured</p><p className="mt-1 font-semibold">{item.measured_count}</p></div></div></CardContent></Card>)}</div></TabsContent>

      <TabsContent value="symbols"><Card><CardHeader><CardTitle className="text-base">Symbol leaderboard</CardTitle></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[900px] text-sm"><thead className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground"><tr><th className="py-3">Symbol</th><th>Sector</th><th>Decisions</th><th>Measured</th><th>Confidence</th><th>Score</th><th>Accuracy</th><th>Avg return</th><th>Latest evidence</th></tr></thead><tbody>{symbolRows.map(item => <tr key={item.symbol} className="border-b border-border/60"><td className="py-3 font-semibold text-primary">{item.symbol}</td><td>{item.sector}</td><td>{item.decision_count}</td><td>{item.measured_count}</td><td>{item.average_confidence_percent}%</td><td>{item.average_score}</td><td>{item.directional_accuracy_percent}%</td><td className={cn(item.average_return_percent > 0 && "text-emerald-400", item.average_return_percent < 0 && "text-red-400")}>{item.average_return_percent}%</td><td className="max-w-[320px] truncate text-muted-foreground" title={item.latest_headline}>{item.latest_headline || "—"}</td></tr>)}</tbody></table>{!symbolRows.length && <div className="py-10 text-center text-sm text-muted-foreground">No symbol decisions in this period.</div>}</CardContent></Card></TabsContent>

      <TabsContent value="blockers" className="space-y-4"><div className="grid gap-4 xl:grid-cols-[2fr_1fr]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><XCircle className="h-4 w-4 text-red-400" />Why decisions were blocked</CardTitle></CardHeader><CardContent className="space-y-3">{data.blocker_analytics.top_blockers.map((item, index) => <div key={`${item.reason}-${index}`} className="rounded-md border p-4"><div className="flex items-start justify-between gap-4"><p className="text-sm leading-6">{item.reason}</p><span className="rounded-full bg-red-500/10 px-2.5 py-1 text-xs font-semibold text-red-400">{item.count}</span></div><p className="mt-2 text-xs text-muted-foreground">Affected {item.symbol_count} symbols{item.symbols.length ? ` · ${item.symbols.join(", ")}` : ""}</p></div>)}</CardContent></Card><Card><CardHeader><CardTitle className="text-base">Blocking summary</CardTitle></CardHeader><CardContent className="space-y-4"><MetricCard title="Blocker Events" value={data.blocker_analytics.total_blocker_events.toLocaleString()} detail="Across shadow and memory decisions" icon={XCircle} /><MetricCard title="Unique Reasons" value={data.blocker_analytics.unique_blockers.toLocaleString()} detail="Distinct safety or readiness constraints" icon={ShieldCheck} /></CardContent></Card></div></TabsContent>
    </Tabs>
  </div>;
}
