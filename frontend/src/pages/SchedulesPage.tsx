import React, { useState } from "react";
import { Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusBadge } from "@/components/StatusBadge";
import { ScheduleFormDialog } from "@/components/ScheduleFormDialog";
import {
  useScheduleList,
  useSchedulerStatus,
  useCreateSchedule,
  useUpdateSchedule,
  useEnableSchedule,
  useDisableSchedule,
  useRunScheduleNow,
  useDeleteSchedule,
} from "@/hooks/useSchedules";
import { formatCadence, formatCountdown } from "@/lib/schedule-utils";
import {
  ScheduledTask,
  ScheduleWriteRequest,
} from "@/lib/types";
import { formatDate, cn } from "@/lib/utils";
import {
  CalendarClock,
  Plus,
  MoreHorizontal,
  Play,
  Pencil,
  Trash2,
  Power,
  PowerOff,
  AlertTriangle,
  RefreshCw,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Server,
} from "lucide-react";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function schedulerStatusDot(status: string, online: boolean): string {
  if (!online) return "bg-destructive";
  const s = status.toUpperCase();
  if (s === "IDLE" || s === "ONLINE") return "bg-emerald-500";
  if (s === "BUSY") return "bg-blue-400 animate-pulse";
  if (s === "STALE" || s === "DEGRADED") return "bg-amber-400";
  if (["STOPPED", "NOT_SEEN", "OFFLINE"].includes(s)) return "bg-destructive";
  return "bg-emerald-500";
}

function schedulerStatusText(status: string, online: boolean): string {
  if (!online) return "text-destructive";
  const s = status.toUpperCase();
  if (s === "IDLE" || s === "ONLINE") return "text-emerald-400";
  if (s === "BUSY") return "text-blue-400";
  if (s === "STALE" || s === "DEGRADED") return "text-amber-400";
  if (["STOPPED", "NOT_SEEN", "OFFLINE"].includes(s)) return "text-destructive";
  return "text-emerald-400";
}

function fmtHeartbeat(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const s = Math.round(seconds);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

function taskTypeLabel(t: string): string {
  const labels: Record<string, string> = {
    INTELLIGENCE_CYCLE: "Intelligence Cycle",
    NEWS_RESEARCH_CYCLE: "News Research",
    STRATEGY_REPORT: "Strategy Report",
    SHADOW_ANALYSIS: "Shadow Analysis",
  };
  return labels[t] ?? t.replace(/_/g, " ");
}

function earliestEnabled(schedules: ScheduledTask[]): ScheduledTask | null {
  const enabled = schedules.filter((s) => s.enabled && s.next_run_at);
  if (!enabled.length) return null;
  return enabled.reduce((a, b) =>
    new Date(a.next_run_at!).getTime() < new Date(b.next_run_at!).getTime() ? a : b,
  );
}

// ─── Scheduler Status Header ──────────────────────────────────────────────────

function SchedulerStatusHeader() {
  const { data: status, isLoading, isError, refetch } = useSchedulerStatus(true);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4">
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !status) {
    return (
      <Card className="border-destructive/30">
        <CardContent className="p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-destructive text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            Scheduler status unavailable
          </div>
          <Button size="sm" variant="outline" onClick={() => refetch()}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const meta = status.metadata;
  const dotCls = schedulerStatusDot(status.status, status.online);
  const textCls = schedulerStatusText(status.status, status.online);

  return (
    <Card data-testid="scheduler-status-header">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Server className="w-3.5 h-3.5" />
          Scheduler Process
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-start gap-3">
          <div className={cn("mt-1 w-2.5 h-2.5 rounded-full shrink-0", dotCls)} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="text-sm font-semibold">Automation Scheduler</span>
              <span className={cn("text-xs font-bold uppercase tracking-wide", textCls)}>
                {status.status}
              </span>
              {!status.online && (
                <span className="text-[10px] text-destructive bg-destructive/10 border border-destructive/20 px-1.5 py-0.5 rounded font-semibold uppercase">
                  OFFLINE
                </span>
              )}
            </div>
            {status.detail && (
              <p className="text-xs text-muted-foreground mb-2">{status.detail}</p>
            )}
            <div className="flex flex-wrap gap-x-5 gap-y-0.5 text-[11px] text-muted-foreground">
              {meta.heartbeat_age_seconds != null && (
                <span>Heartbeat: {fmtHeartbeat(meta.heartbeat_age_seconds)}</span>
              )}
              {meta.process_id != null && (
                <span className="font-mono">PID {meta.process_id}</span>
              )}
              {meta.tasks_processed != null && (
                <span>{meta.tasks_processed} tasks processed</span>
              )}
              {meta.started_at && (
                <span>Started: {formatDate(meta.started_at)}</span>
              )}
              {meta.current_schedule_id && (
                <span className="font-mono">
                  Running schedule: {meta.current_schedule_id}
                </span>
              )}
              {meta.current_task_type && (
                <span>Task: {taskTypeLabel(meta.current_task_type)}</span>
              )}
              {meta.last_error && (
                <span className="text-destructive" title={meta.last_error}>
                  Last error: {meta.last_error.slice(0, 80)}
                  {meta.last_error.length > 80 ? "…" : ""}
                </span>
              )}
            </div>
          </div>
        </div>

        {!status.online && (
          <div className="mt-3 flex items-start gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-md px-3 py-2">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>
              Scheduler process is not running. Start{" "}
              <code className="font-mono">python -m app.run_scheduler</code> on the
              host to enable automated schedules.
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Summary Cards ────────────────────────────────────────────────────────────

function SummaryCards({ schedules }: { schedules: ScheduledTask[] }) {
  const total = schedules.length;
  const enabled = schedules.filter((s) => s.enabled).length;
  const disabled = total - enabled;
  const next = earliestEnabled(schedules);

  const cards = [
    {
      label: "Total Schedules",
      value: total,
      icon: CalendarClock,
      color: "text-foreground",
    },
    {
      label: "Enabled",
      value: enabled,
      icon: CheckCircle2,
      color: "text-emerald-400",
    },
    {
      label: "Disabled",
      value: disabled,
      icon: XCircle,
      color: disabled > 0 ? "text-muted-foreground" : "text-muted-foreground",
    },
    {
      label: "Next Scheduled",
      value: next
        ? `${taskTypeLabel(next.task_type)} — ${formatDate(next.next_run_at)}`
        : "None",
      icon: Clock,
      color: next ? "text-primary" : "text-muted-foreground",
      isText: true,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <Card key={c.label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {c.label}
                </span>
              </div>
              {c.isText ? (
                <p className={cn("text-xs font-medium truncate", c.color)}>{c.value}</p>
              ) : (
                <p className={cn("text-2xl font-black font-mono", c.color)}>{c.value}</p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ─── Action row component ──────────────────────────────────────────────────────

function ScheduleActions({
  schedule,
  onEdit,
}: {
  schedule: ScheduledTask;
  onEdit: (s: ScheduledTask) => void;
}) {
  const [runConfirmOpen, setRunConfirmOpen] = useState(false);
  const [disableConfirmOpen, setDisableConfirmOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const enableMut = useEnableSchedule();
  const disableMut = useDisableSchedule();
  const runNowMut = useRunScheduleNow();
  const deleteMut = useDeleteSchedule();

  const anyPending =
    enableMut.isPending ||
    disableMut.isPending ||
    runNowMut.isPending ||
    deleteMut.isPending;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            disabled={anyPending}
            data-testid={`schedule-actions-${schedule.schedule_id}`}
          >
            {anyPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <MoreHorizontal className="w-3.5 h-3.5" />
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() => setRunConfirmOpen(true)}
            data-testid={`run-now-${schedule.schedule_id}`}
          >
            <Play className="w-3.5 h-3.5 mr-2" />
            Run Now
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onEdit(schedule)}>
            <Pencil className="w-3.5 h-3.5 mr-2" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          {schedule.enabled ? (
            <DropdownMenuItem
              onClick={() => setDisableConfirmOpen(true)}
              data-testid={`disable-${schedule.schedule_id}`}
            >
              <PowerOff className="w-3.5 h-3.5 mr-2" />
              Disable
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem
              onClick={() => enableMut.mutate(schedule.schedule_id)}
              data-testid={`enable-${schedule.schedule_id}`}
            >
              <Power className="w-3.5 h-3.5 mr-2" />
              Enable
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={() => setDeleteConfirmOpen(true)}
            className="text-destructive focus:text-destructive"
            data-testid={`delete-${schedule.schedule_id}`}
          >
            <Trash2 className="w-3.5 h-3.5 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Run Now confirm */}
      <AlertDialog open={runConfirmOpen} onOpenChange={setRunConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Run Now?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately queue a {taskTypeLabel(schedule.task_type)} job
              for schedule <span className="font-mono">{schedule.schedule_id}</span>.
              The job will be queued regardless of market hours.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                runNowMut.mutate(schedule.schedule_id);
                setRunConfirmOpen(false);
              }}
            >
              Queue Run
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Disable confirm */}
      <AlertDialog open={disableConfirmOpen} onOpenChange={setDisableConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable Schedule?</AlertDialogTitle>
            <AlertDialogDescription>
              <span className="font-mono">{schedule.schedule_id}</span> will stop
              running automatically. You can re-enable it at any time.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                disableMut.mutate(schedule.schedule_id);
                setDisableConfirmOpen(false);
              }}
              className="bg-amber-500 hover:bg-amber-600 text-white"
            >
              Disable
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete confirm */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Schedule?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete schedule{" "}
              <span className="font-mono">{schedule.schedule_id}</span>. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                deleteMut.mutate(schedule.schedule_id);
                setDeleteConfirmOpen(false);
              }}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function SchedulesPage() {
  const { data: schedulesResp, isLoading, isError, refetch } = useScheduleList();
  const schedules = schedulesResp?.items ?? [];

  const [formOpen, setFormOpen] = useState(false);
  const [editSchedule, setEditSchedule] = useState<ScheduledTask | null>(null);

  const createMut = useCreateSchedule();

  // useUpdateSchedule requires a scheduleId — we derive it from editSchedule
  const updateMutRef = React.useRef<ReturnType<typeof useUpdateSchedule> | null>(null);

  // We can't conditionally call hooks, so we always call it but with a placeholder
  // when not editing. The mutationFn is only called on submit.
  const updateMut = useUpdateSchedule(editSchedule?.schedule_id ?? "__none__");

  const handleOpenCreate = () => {
    setEditSchedule(null);
    setFormOpen(true);
  };

  const handleOpenEdit = (s: ScheduledTask) => {
    setEditSchedule(s);
    setFormOpen(true);
  };

  const handleFormSubmit = (req: ScheduleWriteRequest) => {
    if (editSchedule) {
      updateMut.mutate(req, {
        onSuccess: () => setFormOpen(false),
      });
    } else {
      createMut.mutate(req, {
        onSuccess: () => setFormOpen(false),
      });
    }
  };

  const isPending = editSchedule ? updateMut.isPending : createMut.isPending;

  return (
    <div className="space-y-5 max-w-7xl">
      {/* ── Page header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider">
            Automation Scheduler
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage automated research schedules. Paper-trading start and stop remain
            manual.
          </p>
        </div>
        <Button onClick={handleOpenCreate} size="sm" data-testid="btn-create-schedule">
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          New Schedule
        </Button>
      </div>

      {/* ── Safety notice ─────────────────────────────────────────────────── */}
      <div
        className="flex items-start gap-2 px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400"
        data-testid="safety-notice"
      >
        <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
        <span>
          <strong>Research automation only.</strong> Scheduled tasks run research
          pipelines. Paper-trading start and stop remain manual and are not schedulable
          here.
        </span>
      </div>

      {/* ── Scheduler process status ─────────────────────────────────────── */}
      <SchedulerStatusHeader />

      {/* ── Summary cards ─────────────────────────────────────────────────── */}
      {!isLoading && !isError && (
        <SummaryCards schedules={schedules} />
      )}

      {/* ── Schedule table ─────────────────────────────────────────────────── */}
      <Card>
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-muted-foreground" />
          <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground flex-1">
            Schedules ({schedules.length})
          </h3>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => refetch()}
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-8 text-center space-y-3">
            <AlertTriangle className="w-5 h-5 text-muted-foreground mx-auto" />
            <p className="text-sm text-muted-foreground">
              Failed to load schedules.
            </p>
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry
            </Button>
          </div>
        ) : schedules.length === 0 ? (
          <div
            className="p-12 text-center space-y-3"
            data-testid="schedules-empty-state"
          >
            <CalendarClock className="w-8 h-8 text-muted-foreground/40 mx-auto" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                No schedules configured
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Create a schedule to automate research pipelines.
              </p>
            </div>
            <Button
              size="sm"
              onClick={handleOpenCreate}
              data-testid="btn-create-first-schedule"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Create First Schedule
            </Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>ID</TableHead>
                <TableHead>Task</TableHead>
                <TableHead>Cadence</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Next Run</TableHead>
                <TableHead>Last Run</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.map((s) => {
                const secsUntil = s.next_run_at
                  ? (new Date(s.next_run_at).getTime() - Date.now()) / 1000
                  : null;
                return (
                  <TableRow key={s.schedule_id} data-testid={`schedule-row-${s.schedule_id}`}>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {s.schedule_id.slice(0, 8)}…
                    </TableCell>
                    <TableCell className="text-sm font-medium">
                      {taskTypeLabel(s.task_type)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatCadence(s)}
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full",
                          s.enabled
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-muted text-muted-foreground border border-border",
                        )}
                      >
                        {s.enabled ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <XCircle className="w-3 h-3" />
                        )}
                        {s.enabled ? "Enabled" : "Disabled"}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs font-mono">
                      {secsUntil != null ? (
                        <span className={secsUntil <= 0 ? "text-amber-400 font-semibold" : ""}>
                          {formatCountdown(secsUntil)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {s.last_run_at ? formatDate(s.last_run_at) : "—"}
                    </TableCell>
                    <TableCell>
                      <ScheduleActions schedule={s} onEdit={handleOpenEdit} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* ── Create / Edit dialog ──────────────────────────────────────────── */}
      <ScheduleFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        editSchedule={editSchedule}
        onSubmit={handleFormSubmit}
        isPending={isPending}
      />
    </div>
  );
}
