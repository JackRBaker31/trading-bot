import React, { useMemo, useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Job, ListResponse } from "@/lib/types";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { X, Zap, AlertTriangle, ShieldCheck } from "lucide-react";
import { formatDistanceStrict, parseISO } from "date-fns";

// ─── Human-readable job type labels ──────────────────────────────────────────

const JOB_TYPE_LABELS: Record<string, string> = {
  NEWS_RESEARCH_CYCLE:   "News Research",
  STRATEGY_REPORT:       "Strategy Report",
  SHADOW_ANALYSIS:       "Shadow Analysis",
  INTELLIGENCE_CYCLE:    "Intelligence Cycle",
  RECONCILIATION:        "Reconciliation",
  DATA_SYNC:             "Data Sync",
  BROKER_SYNC:           "Broker Sync",
  PORTFOLIO_SNAPSHOT:    "Portfolio Snapshot",
  PRICE_REFRESH:         "Price Refresh",
  SIGNAL_SCAN:           "Signal Scan",
};

function readableJobType(raw: string): string {
  return JOB_TYPE_LABELS[raw] ?? raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function calcDuration(started?: string | null, finished?: string | null): string {
  if (!started || !finished) return "—";
  try {
    return formatDistanceStrict(parseISO(started), parseISO(finished));
  } catch {
    return "—";
  }
}

/** Suppress stack trace content — never display raw exception traces. */
function sanitizeText(text: string): string {
  if (
    text.includes("Traceback (most recent call last)") ||
    text.includes('File "') ||
    text.length > 2000
  ) {
    return "[Error details hidden]";
  }
  return text;
}

function sanitizePayloadValue(v: unknown): string {
  if (v == null) return "—";
  const s = typeof v === "object" ? JSON.stringify(v) : String(v);
  return sanitizeText(s);
}

// ─── Job Detail Drawer ────────────────────────────────────────────────────────

function JobDetailDrawer({ job, onClose }: { job: Job | null; onClose: () => void }) {
  if (!job) return null;

  const payloadEntries = Object.entries(job.payload ?? {});
  const resultEntries = Object.entries(job.result ?? {}).filter(([, v]) => v != null);

  return (
    <Sheet open={!!job} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-3 flex-wrap">
            <SheetTitle className="text-lg font-black">
              {readableJobType(job.job_type)}
            </SheetTitle>
            <StatusBadge status={job.status} />
          </div>
          <p className="font-mono text-xs text-muted-foreground mt-1 break-all">
            {job.job_id}
          </p>
        </SheetHeader>

        <div className="space-y-6">
          {/* Timing */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Timing
            </p>
            <div className="space-y-1.5">
              {[
                { label: "Created",  value: formatDate(job.created_at) },
                { label: "Started",  value: formatDate(job.started_at) },
                { label: "Finished", value: formatDate(job.finished_at) },
                { label: "Duration", value: calcDuration(job.started_at, job.finished_at) },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-mono text-xs">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Payload */}
          {payloadEntries.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Job Parameters
              </p>
              <div className="space-y-1.5">
                {payloadEntries.map(([k, v]) => (
                  <div key={k} className="flex justify-between items-start gap-4 text-sm">
                    <span className="text-muted-foreground capitalize shrink-0">
                      {k.replace(/_/g, " ")}
                    </span>
                    <span className="font-mono text-xs text-right break-all">
                      {sanitizePayloadValue(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Result summary */}
          {resultEntries.length > 0 && (() => {
            const result = job.result ?? {};
            const tradingImpact = typeof result.trading_impact === "string"
              ? result.trading_impact
              : null;
            const stages = Array.isArray(result.stages) ? result.stages : null;
            const isIntelligenceCycle = job.job_type === "INTELLIGENCE_CYCLE";

            const STAGE_ORDER = [
              "NEWS_RESEARCH",
              "CAPTURE_PRICE_OUTCOMES",
              "SHADOW_ANALYSIS",
              "SHADOW_PERFORMANCE",
              "GRADUATION_STATUS",
              "INTELLIGENCE_SNAPSHOT",
              "DAILY_BRIEFING",
            ];

            function stageSortKey(s: Record<string, unknown>) {
              const name = String(s.stage_name ?? s.name ?? "");
              const idx = STAGE_ORDER.indexOf(name.toUpperCase());
              return idx >= 0 ? idx : 999;
            }

            const sortedStages = stages
              ? [...stages].sort((a, b) =>
                  stageSortKey(a as Record<string, unknown>) -
                  stageSortKey(b as Record<string, unknown>),
                )
              : null;

            return (
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Result
                </p>

                {/* Trading impact safety badge */}
                {tradingImpact && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 mb-3">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="text-xs font-semibold text-emerald-400">
                      Trading impact: {tradingImpact}
                    </span>
                    <span className="text-xs text-emerald-400/70">— Research only</span>
                  </div>
                )}

                {/* Stage breakdown for INTELLIGENCE_CYCLE */}
                {isIntelligenceCycle && sortedStages && sortedStages.length > 0 ? (
                  <div className="space-y-2" data-testid="ic-stage-breakdown">
                    {sortedStages.map((stageRaw, i) => {
                      const stage = stageRaw as Record<string, unknown>;
                      const stageName = String(stage.stage_name ?? stage.name ?? `Stage ${i + 1}`);
                      const stageStatus = String(stage.status ?? "UNKNOWN").toUpperCase();
                      const summary = typeof stage.summary === "string" ? stage.summary : null;
                      const warning = typeof stage.warning_text === "string"
                        ? stage.warning_text
                        : typeof stage.warning === "string"
                          ? stage.warning
                          : null;
                      const errorTxt = typeof stage.error_text === "string"
                        ? stage.error_text
                        : typeof stage.error === "string"
                          ? stage.error
                          : null;

                      const isOk = ["SUCCESS", "OK", "COMPLETED", "DONE"].includes(stageStatus);
                      const isFail = ["FAILED", "ERROR", "SKIPPED"].includes(stageStatus);

                      return (
                        <div
                          key={i}
                          className={cn(
                            "rounded-lg border px-3 py-2 space-y-1",
                            isOk
                              ? "bg-emerald-500/5 border-emerald-500/20"
                              : isFail
                                ? "bg-destructive/5 border-destructive/20"
                                : "bg-muted/30 border-border",
                          )}
                          data-testid={`ic-stage-${stageName.toLowerCase().replace(/ /g, "-")}`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-semibold capitalize">
                              {stageName.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}
                            </span>
                            <span
                              className={cn(
                                "text-[10px] font-bold uppercase",
                                isOk ? "text-emerald-400" : isFail ? "text-destructive" : "text-muted-foreground",
                              )}
                            >
                              {stageStatus}
                            </span>
                          </div>
                          {summary && (
                            <p className="text-[11px] text-muted-foreground">{summary}</p>
                          )}
                          {warning && (
                            <p className="text-[11px] text-amber-400 flex items-start gap-1">
                              <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                              {warning}
                            </p>
                          )}
                          {errorTxt && (
                            <p className="text-[11px] text-destructive flex items-start gap-1">
                              <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                              {errorTxt}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  /* Generic result for non-INTELLIGENCE_CYCLE or when no stages */
                  <div className="space-y-1.5">
                    {resultEntries
                      .filter(([k]) => k !== "stages" && k !== "trading_impact")
                      .map(([k, v]) => (
                        <div key={k} className="flex justify-between items-start gap-4 text-sm">
                          <span className="text-muted-foreground capitalize shrink-0">
                            {k.replace(/_/g, " ")}
                          </span>
                          <span className="font-mono text-xs text-right break-all">
                            {sanitizePayloadValue(v)}
                          </span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            );
          })()}

          {/* Error */}
          {(job.error_code || job.error_summary) && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-destructive shrink-0" />
                <p className="text-xs font-semibold uppercase tracking-wider text-destructive">
                  Error
                </p>
              </div>
              {job.error_code && (
                <p className="text-xs font-mono text-destructive/80 mb-1">
                  Code: {job.error_code}
                </p>
              )}
              {job.error_summary && (
                <p className="text-xs text-destructive/80 leading-relaxed">
                  {sanitizeText(job.error_summary)}
                </p>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function JobsPage() {
  // ── Filter state ─────────────────────────────────────────────────────────
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [activeOnly, setActiveOnly] = useState(false);
  const [failedOnly, setFailedOnly] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // ── Drawer ───────────────────────────────────────────────────────────────
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  // ── Query ─────────────────────────────────────────────────────────────────
  const { data: jobsResp, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => apiClient.get<ListResponse<Job>>("/jobs"),
    refetchInterval: 5000,
  });

  const allJobs = jobsResp?.items ?? [];

  // Derive unique job types from the data
  const jobTypes = useMemo(() => {
    const types = new Set(allJobs.map((j) => j.job_type));
    return Array.from(types).sort();
  }, [allJobs]);

  // ── Filtering ─────────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    return allJobs.filter((j) => {
      if (typeFilter !== "ALL" && j.job_type !== typeFilter) return false;
      if (statusFilter !== "ALL" && j.status !== statusFilter) return false;
      if (activeOnly && !["QUEUED", "RUNNING"].includes(j.status)) return false;
      if (failedOnly && j.status !== "FAILED") return false;
      if (dateFrom && new Date(j.created_at) < new Date(dateFrom)) return false;
      if (dateTo && new Date(j.created_at) > new Date(dateTo + "T23:59:59")) return false;
      return true;
    });
  }, [allJobs, typeFilter, statusFilter, activeOnly, failedOnly, dateFrom, dateTo]);

  const activeJobs = filtered.filter((j) => ["QUEUED", "RUNNING"].includes(j.status));
  const completedJobs = filtered.filter((j) => !["QUEUED", "RUNNING"].includes(j.status));

  const hasFilters = !!(
    typeFilter !== "ALL" || statusFilter !== "ALL" || activeOnly || failedOnly || dateFrom || dateTo
  );

  const resetFilters = () => {
    setTypeFilter("ALL");
    setStatusFilter("ALL");
    setActiveOnly(false);
    setFailedOnly(false);
    setDateFrom("");
    setDateTo("");
  };

  return (
    <div className="space-y-5 max-w-7xl">
      <h2 className="text-sm font-semibold uppercase tracking-wider">Job Runner</h2>

      {/* ── Filter toolbar ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg border border-border bg-card/50">
        {/* Job type */}
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="h-8 text-xs w-44">
            <SelectValue placeholder="Job Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Types</SelectItem>
            {jobTypes.map((t) => (
              <SelectItem key={t} value={t}>
                {readableJobType(t)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Status */}
        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v);
            if (v !== "ALL") { setActiveOnly(false); setFailedOnly(false); }
          }}
        >
          <SelectTrigger className="h-8 text-xs w-44">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Statuses</SelectItem>
            <SelectItem value="QUEUED">Queued</SelectItem>
            <SelectItem value="RUNNING">Running</SelectItem>
            <SelectItem value="SUCCEEDED">Succeeded</SelectItem>
            <SelectItem value="SUCCEEDED_WITH_WARNINGS">Succeeded w/ Warnings</SelectItem>
            <SelectItem value="FAILED">Failed</SelectItem>
            <SelectItem value="CANCELLED">Cancelled</SelectItem>
          </SelectContent>
        </Select>

        <div className="w-px h-5 bg-border" />

        {/* Active-only quick filter */}
        <button
          onClick={() => { setActiveOnly((v) => !v); setFailedOnly(false); setStatusFilter("ALL"); }}
          className={cn(
            "flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-[11px] font-bold uppercase tracking-wide transition-colors",
            activeOnly
              ? "bg-primary text-primary-foreground border-primary"
              : "text-muted-foreground border-border hover:border-muted-foreground/50",
          )}
        >
          <Zap className="w-3 h-3" />
          Active
        </button>

        {/* Failed-only quick filter */}
        <button
          onClick={() => { setFailedOnly((v) => !v); setActiveOnly(false); setStatusFilter("ALL"); }}
          className={cn(
            "flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-[11px] font-bold uppercase tracking-wide transition-colors",
            failedOnly
              ? "bg-destructive text-destructive-foreground border-destructive"
              : "text-muted-foreground border-border hover:border-muted-foreground/50",
          )}
        >
          <AlertTriangle className="w-3 h-3" />
          Failed
        </button>

        <div className="w-px h-5 bg-border" />

        {/* Date range */}
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="h-8 rounded border border-border bg-background text-xs px-2 text-foreground"
            title="From date"
          />
          <span className="text-muted-foreground text-xs">–</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="h-8 rounded border border-border bg-background text-xs px-2 text-foreground"
            title="To date"
          />
        </div>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="text-muted-foreground h-8">
            <X className="w-3.5 h-3.5 mr-1" />
            Reset
          </Button>
        )}
      </div>

      {/* ── Active jobs ────────────────────────────────────────────────────── */}
      {activeJobs.length > 0 && (
        <Card className="border-accent/30">
          <div className="px-4 py-3 border-b border-accent/20 bg-accent/5">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-accent flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              Active Operations ({activeJobs.length})
            </h3>
          </div>
          <JobTable jobs={activeJobs} onSelect={setSelectedJob} />
        </Card>
      )}

      {/* ── Job history ───────────────────────────────────────────────────── */}
      <Card>
        <div className="px-4 py-3 border-b">
          <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Job History ({completedJobs.length})
          </h3>
        </div>
        <JobTable jobs={completedJobs} isLoading={isLoading} onSelect={setSelectedJob} />
      </Card>

      {/* Detail drawer */}
      <JobDetailDrawer job={selectedJob} onClose={() => setSelectedJob(null)} />
    </div>
  );
}

// ─── Jobs Table ───────────────────────────────────────────────────────────────

function JobTable({
  jobs,
  isLoading,
  onSelect,
}: {
  jobs: Job[];
  isLoading?: boolean;
  onSelect: (job: Job) => void;
}) {
  if (isLoading) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Job ID</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Duration</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 4 }).map((_, i) => (
            <TableRow key={i}>
              <TableCell colSpan={5}>
                <Skeleton className="h-5 w-full" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }

  if (!jobs.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">No jobs found.</div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead className="w-[120px]">Job ID</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Duration</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => (
          <TableRow
            key={job.job_id}
            className="cursor-pointer hover:bg-muted/40"
            onClick={() => onSelect(job)}
          >
            <TableCell className="font-mono text-xs text-muted-foreground">
              {job.job_id.substring(0, 8)}…
            </TableCell>
            <TableCell className="text-sm font-medium">
              {readableJobType(job.job_type)}
            </TableCell>
            <TableCell>
              <StatusBadge status={job.status} />
            </TableCell>
            <TableCell className="text-xs text-muted-foreground">
              {formatDate(job.created_at)}
            </TableCell>
            <TableCell className="text-xs font-mono">
              {calcDuration(job.started_at, job.finished_at)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
