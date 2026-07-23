import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  CircleDot,
  Clock3,
  Database,
  Gauge,
  HardDrive,
  Radio,
  RefreshCw,
  ServerCog,
  ShieldCheck,
  Workflow,
  XCircle,
} from "lucide-react";
import { Link } from "wouter";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useOperationsCentre } from "@/hooks/useOperationsCentre";
import { Job, RunHistoryRecord, ScheduledTask, SupervisorMetadata } from "@/lib/types";
import { cn } from "@/lib/utils";

const HEALTHY = new Set(["HEALTHY", "ONLINE", "RUNNING", "IDLE", "CURRENT", "CONFIGURED"]);
const WARNING = new Set(["DEGRADED", "STALE", "BUSY", "STARTING", "STOP_REQUESTED", "SUCCEEDED_WITH_WARNINGS"]);

function friendly(value: string | null | undefined): string {
  if (!value) return "Unknown";
  return value
    .replace(/_CYCLE$/, " Cycle")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "Not scheduled";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not scheduled";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatRelative(value: string | null | undefined): string {
  if (!value) return "Unavailable";
  const ms = new Date(value).getTime() - Date.now();
  if (!Number.isFinite(ms)) return "Unavailable";
  const future = ms >= 0;
  const seconds = Math.max(0, Math.round(Math.abs(ms) / 1000));
  if (seconds < 60) return future ? `in ${seconds}s` : `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return future ? `in ${minutes}m` : `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return future ? `in ${hours}h` : `${hours}h ago`;
  const days = Math.round(hours / 24);
  return future ? `in ${days}d` : `${days}d ago`;
}

function statusClasses(status: string | undefined): string {
  const value = status?.toUpperCase() ?? "UNKNOWN";
  if (HEALTHY.has(value)) return "border-emerald-500/25 bg-emerald-500/[0.055]";
  if (WARNING.has(value)) return "border-amber-500/30 bg-amber-500/[0.06]";
  return "border-red-500/30 bg-red-500/[0.065]";
}

function statusDot(status: string | undefined): string {
  const value = status?.toUpperCase() ?? "UNKNOWN";
  if (HEALTHY.has(value)) return "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]";
  if (WARNING.has(value)) return "bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.75)]";
  return "bg-red-400 shadow-[0_0_12px_rgba(248,113,113,0.75)]";
}

function isToday(value: string | null | undefined): boolean {
  if (!value) return false;
  const date = new Date(value);
  const now = new Date();
  return date.toDateString() === now.toDateString();
}

function RackRow({
  label,
  status,
  detail,
  icon: Icon,
}: {
  label: string;
  status: string;
  detail: string;
  icon: typeof Activity;
}) {
  return (
    <div className={cn("group grid grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-border/55 px-4 py-3 last:border-0", statusClasses(status))}>
      <div className="relative flex h-9 w-9 items-center justify-center rounded-md border border-border/70 bg-background/50">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span className={cn("absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full", statusDot(status))} />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold">{label}</p>
        <p className="truncate text-xs text-muted-foreground">{detail}</p>
      </div>
      <StatusBadge status={status} />
    </div>
  );
}

function TimelineIcon({ status }: { status: string }) {
  if (status === "FAILED") return <XCircle className="h-4 w-4 text-red-400" />;
  if (status === "RUNNING" || status === "QUEUED") return <Radio className="h-4 w-4 animate-pulse text-amber-400" />;
  if (status === "SUCCEEDED_WITH_WARNINGS") return <AlertTriangle className="h-4 w-4 text-amber-400" />;
  return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
}

interface TimelineItem {
  id: string;
  time: string | null;
  title: string;
  detail: string;
  status: string;
}

function jobTimelineItem(job: Job): TimelineItem {
  const time = job.finished_at ?? job.started_at ?? job.created_at;
  const duration = job.duration_seconds == null ? null : `${job.duration_seconds.toFixed(1)}s`;
  return {
    id: `job-${job.job_id}`,
    time,
    title: `${friendly(job.job_type)} ${friendly(job.status)}`,
    detail: job.error_summary ?? (duration ? `Completed in ${duration}` : `Job ${job.job_id}`),
    status: job.status,
  };
}

function runTimelineItem(run: RunHistoryRecord): TimelineItem {
  return {
    id: `run-${run.run_id}`,
    time: run.finished_at ?? run.started_at,
    title: `${friendly(run.run_type)} ${friendly(run.status)}`,
    detail: run.error_summary ?? `${run.created_count} created · ${run.skipped_count} skipped · ${run.failure_count} failed`,
    status: run.status,
  };
}

export default function OperationsPage() {
  const operations = useOperationsCentre();
  const [refreshing, setRefreshing] = useState(false);

  const infrastructure = operations.infrastructure.data;
  const jobs = operations.jobs.data?.items ?? [];
  const runHistory = operations.runHistory.data?.items ?? [];
  const schedules = operations.schedules.data?.items ?? [];
  const paperTrading = operations.paperTrading.data;
  const scheduler = operations.scheduler.data;
  const appStatus = operations.appStatus.data;

  const supervisor = infrastructure?.services.supervisor;
  const supervisorMeta = supervisor?.metadata as unknown as SupervisorMetadata | undefined;
  const activeJobs = useMemo(
    () => jobs.filter((job) => job.status === "RUNNING" || job.status === "QUEUED"),
    [jobs],
  );
  const currentJob = activeJobs.find((job) => job.status === "RUNNING") ?? activeJobs[0];

  const upcoming = useMemo(
    () => schedules
      .filter((item): item is ScheduledTask & { next_run_at: string } => item.enabled && !!item.next_run_at)
      .sort((a, b) => new Date(a.next_run_at).getTime() - new Date(b.next_run_at).getTime())
      .slice(0, 6),
    [schedules],
  );

  const timeline = useMemo(
    () => [...jobs.map(jobTimelineItem), ...runHistory.map(runTimelineItem)]
      .sort((a, b) => new Date(b.time ?? 0).getTime() - new Date(a.time ?? 0).getTime())
      .slice(0, 12),
    [jobs, runHistory],
  );

  const issues = useMemo(() => {
    const result: Array<{ title: string; detail: string }> = [];
    if (infrastructure) {
      Object.entries(infrastructure.services).forEach(([name, service]) => {
        const status = service.status.toUpperCase();
        if (!service.online || ["FAILED", "STALE", "STOPPED", "NOT_SEEN"].includes(status)) {
          result.push({ title: `${friendly(name)} ${friendly(service.status)}`, detail: service.detail });
        }
      });
    }
    jobs.filter((job) => job.status === "FAILED").slice(0, 4).forEach((job) => {
      result.push({ title: `${friendly(job.job_type)} failed`, detail: job.error_summary ?? "Open Jobs for full diagnostics." });
    });
    return result;
  }, [infrastructure, jobs]);

  const completedToday = jobs.filter((job) => isToday(job.finished_at) && ["SUCCEEDED", "SUCCEEDED_WITH_WARNINGS"].includes(job.status)).length;
  const failedToday = jobs.filter((job) => isToday(job.finished_at) && job.status === "FAILED").length;
  const platformStatus = infrastructure?.overall_status ?? "UNKNOWN";
  const healthyCount = supervisorMeta?.healthy_process_count ?? 0;
  const managedCount = supervisorMeta?.managed_process_count ?? 0;
  const statusAge = typeof supervisorMeta?.status_age_seconds === "number"
    ? `${Math.round(supervisorMeta.status_age_seconds)}s`
    : "Unavailable";

  const currentTitle = currentJob
    ? friendly(currentJob.job_type)
    : scheduler?.metadata.current_task_type
      ? friendly(scheduler.metadata.current_task_type)
      : "System idle";
  const currentStatus = currentJob?.status ?? (scheduler?.metadata.current_task_type ? "RUNNING" : "IDLE");
  const currentDetail = currentJob
    ? `Job ${currentJob.job_id} · started ${formatRelative(currentJob.started_at ?? currentJob.created_at)}`
    : upcoming[0]
      ? `Waiting for ${friendly(upcoming[0].task_type)} ${formatRelative(upcoming[0].next_run_at)}`
      : "No active work and no enabled schedule with a next run.";

  const refresh = async () => {
    setRefreshing(true);
    try {
      await operations.refetchAll();
    } finally {
      setRefreshing(false);
    }
  };

  if (operations.infrastructure.isPending && operations.jobs.isPending) {
    return <div className="space-y-5"><Skeleton className="h-36 w-full" /><div className="grid gap-5 xl:grid-cols-[0.8fr_1.4fr_0.8fr]"><Skeleton className="h-[520px]" /><Skeleton className="h-[520px]" /><Skeleton className="h-[520px]" /></div></div>;
  }

  return (
    <div className="space-y-5">
      {issues.length > 0 && (
        <section className="overflow-hidden rounded-2xl border border-red-500/35 bg-red-500/[0.07]">
          <div className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-4">
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3"><AlertTriangle className="h-6 w-6 text-red-400" /></div>
              <div><p className="text-xs font-bold uppercase tracking-[0.22em] text-red-300">Attention required</p><h2 className="mt-1 text-xl font-semibold">{issues[0].title}</h2><p className="mt-1 text-sm text-muted-foreground">{issues[0].detail}</p></div>
            </div>
            <StatusBadge status={platformStatus} />
          </div>
        </section>
      )}

      <section className={cn("relative overflow-hidden rounded-2xl border p-5 md:p-6", statusClasses(platformStatus))}>
        <div className="absolute inset-0 bg-[linear-gradient(110deg,transparent,rgba(212,175,55,0.06),transparent)]" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-border/70 bg-background/50">
              <ServerCog className="h-7 w-7 text-primary" />
              <span className={cn("absolute -right-1 -top-1 h-3.5 w-3.5 rounded-full", statusDot(platformStatus))} />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-primary">KAIRO Operations Centre</p>
              <div className="mt-1 flex flex-wrap items-center gap-3"><h1 className="text-2xl font-semibold tracking-tight md:text-3xl">System {friendly(platformStatus)}</h1><StatusBadge status={platformStatus} /></div>
              <p className="mt-1 text-sm text-muted-foreground">{healthyCount}/{managedCount} supervised processes healthy · status age {statusAge} · automatic recovery {supervisorMeta?.restart_enabled ? "enabled" : "unavailable"}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={refresh} disabled={refreshing}><RefreshCw className={cn("mr-2 h-4 w-4", refreshing && "animate-spin")} />Refresh</Button>
            <Button asChild><Link href="/jobs"><Activity className="mr-2 h-4 w-4" />Open Jobs</Link></Button>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.8fr_1.35fr_0.85fr]">
        <Card className="overflow-hidden border-border/70 bg-card/70">
          <CardHeader className="border-b border-border/60 pb-4"><CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.14em]"><HardDrive className="h-4 w-4 text-primary" />Platform rack</CardTitle></CardHeader>
          <CardContent className="p-0">
            <RackRow label="Supervisor" status={supervisor?.status ?? "NOT_SEEN"} detail={supervisor?.detail ?? "No supervisor record available."} icon={ServerCog} />
            <RackRow label="API" status={infrastructure?.services.api.status ?? "UNKNOWN"} detail={infrastructure?.services.api.detail ?? "Unavailable"} icon={Activity} />
            <RackRow label="Job Worker" status={infrastructure?.services.job_worker.status ?? "UNKNOWN"} detail={infrastructure?.services.job_worker.detail ?? "Unavailable"} icon={Workflow} />
            <RackRow label="Scheduler" status={infrastructure?.services.scheduler.status ?? "UNKNOWN"} detail={infrastructure?.services.scheduler.detail ?? "Unavailable"} icon={CalendarClock} />
            <RackRow label="Storage" status={infrastructure?.services.storage.status ?? "UNKNOWN"} detail={infrastructure?.services.storage.detail ?? "Unavailable"} icon={Database} />
            <RackRow label="Market Data" status={infrastructure?.services.market_data.status ?? "UNKNOWN"} detail={infrastructure?.services.market_data.detail ?? "Unavailable"} icon={Radio} />
            <RackRow label="Broker" status={infrastructure?.services.broker.status ?? "UNKNOWN"} detail={infrastructure?.services.broker.detail ?? "Unavailable"} icon={Gauge} />
          </CardContent>
        </Card>

        <div className="space-y-5">
          <Card className={cn("border-border/70 bg-card/70", currentJob && "border-primary/30")}>
            <CardHeader className="flex-row items-center justify-between border-b border-border/60 pb-4"><CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.14em]"><CircleDot className={cn("h-4 w-4 text-primary", currentJob && "animate-pulse")} />Current activity</CardTitle><StatusBadge status={currentStatus} /></CardHeader>
            <CardContent className="p-6">
              <p className="text-3xl font-semibold tracking-tight">{currentTitle}</p>
              <p className="mt-2 text-sm text-muted-foreground">{currentDetail}</p>
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl border border-border/70 bg-background/35 p-4"><p className="text-[10px] uppercase tracking-[0.17em] text-muted-foreground">Active / queued</p><p className="mt-2 text-2xl font-semibold">{activeJobs.length}</p></div>
                <div className="rounded-xl border border-border/70 bg-background/35 p-4"><p className="text-[10px] uppercase tracking-[0.17em] text-muted-foreground">Completed today</p><p className="mt-2 text-2xl font-semibold">{completedToday}</p></div>
                <div className="rounded-xl border border-border/70 bg-background/35 p-4"><p className="text-[10px] uppercase tracking-[0.17em] text-muted-foreground">Failed today</p><p className={cn("mt-2 text-2xl font-semibold", failedToday > 0 && "text-red-400")}>{failedToday}</p></div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/70">
            <CardHeader className="flex-row items-center justify-between border-b border-border/60 pb-4"><CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.14em]"><Activity className="h-4 w-4 text-primary" />Operational timeline</CardTitle><Button asChild size="sm" variant="ghost"><Link href="/jobs">Full history</Link></Button></CardHeader>
            <CardContent className="max-h-[420px] overflow-y-auto p-0">
              {timeline.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">No operational events recorded.</div> : timeline.map((item, index) => (
                <div key={item.id} className="grid grid-cols-[62px_20px_1fr] gap-3 border-b border-border/50 px-4 py-3 last:border-0">
                  <p className="pt-0.5 text-xs tabular-nums text-muted-foreground">{formatTime(item.time)}</p>
                  <div className="relative flex justify-center"><TimelineIcon status={item.status} />{index < timeline.length - 1 && <span className="absolute top-5 h-[calc(100%+8px)] w-px bg-border" />}</div>
                  <div className="min-w-0"><p className="text-sm font-medium">{item.title}</p><p className="mt-0.5 truncate text-xs text-muted-foreground">{item.detail}</p></div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-5">
          <Card className="border-border/70 bg-card/70">
            <CardHeader className="flex-row items-center justify-between border-b border-border/60 pb-4"><CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.14em]"><Clock3 className="h-4 w-4 text-primary" />Upcoming work</CardTitle><Button asChild size="sm" variant="ghost"><Link href="/schedules">Manage</Link></Button></CardHeader>
            <CardContent className="p-0">
              {upcoming.length === 0 ? <div className="p-6 text-center text-sm text-muted-foreground">No enabled work is scheduled.</div> : upcoming.map((schedule, index) => (
                <div key={schedule.schedule_id} className="border-b border-border/50 px-4 py-4 last:border-0">
                  <div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{friendly(schedule.task_type)}</p><p className="mt-1 text-xs text-muted-foreground">{formatDateTime(schedule.next_run_at)}</p></div><span className={cn("rounded-full border px-2 py-1 text-[10px] font-semibold", index === 0 ? "border-primary/30 bg-primary/10 text-primary" : "border-border text-muted-foreground")}>{formatRelative(schedule.next_run_at)}</span></div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/70">
            <CardHeader className="border-b border-border/60 pb-4"><CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.14em]"><ShieldCheck className="h-4 w-4 text-primary" />Safety state</CardTitle></CardHeader>
            <CardContent className="space-y-4 p-5">
              <div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Paper trading</span><StatusBadge status={paperTrading?.state ?? "UNKNOWN"} /></div>
              <div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Live trading</span><StatusBadge status={appStatus?.real_money_trading_enabled ? "ENABLED" : "DISABLED"} /></div>
              <div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Broker environment</span><span className="text-sm font-semibold">{appStatus?.broker_environment ?? "Unknown"}</span></div>
              <div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Execution permission</span><span className="text-sm font-semibold">{appStatus?.execution_permission_confirmed ? "Confirmed" : "Not confirmed"}</span></div>
              <div className="rounded-xl border border-border/70 bg-background/35 p-3 text-xs leading-relaxed text-muted-foreground">Paper trading remains independently controlled. This page is operational visibility only and cannot start trading or processes.</div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/70">
            <CardHeader className="border-b border-border/60 pb-4"><CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.14em]"><Gauge className="h-4 w-4 text-primary" />Supervisor health</CardTitle></CardHeader>
            <CardContent className="space-y-4 p-5">
              <div><div className="flex justify-between text-xs"><span className="text-muted-foreground">Healthy managed services</span><span>{healthyCount}/{managedCount}</span></div><Progress value={managedCount > 0 ? (healthyCount / managedCount) * 100 : 0} className="mt-2 h-2" /></div>
              <div className="grid grid-cols-2 gap-3"><div className="rounded-lg border border-border/70 p-3"><p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Recovering</p><p className="mt-1 text-xl font-semibold">{supervisorMeta?.recovering_process_count ?? 0}</p></div><div className="rounded-lg border border-border/70 p-3"><p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Failed</p><p className={cn("mt-1 text-xl font-semibold", (supervisorMeta?.failed_process_count ?? 0) > 0 && "text-red-400")}>{supervisorMeta?.failed_process_count ?? 0}</p></div></div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
