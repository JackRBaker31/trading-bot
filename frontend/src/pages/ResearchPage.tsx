import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Job, ListResponse, ResearchReportResponse } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate, formatGBP, cn } from "@/lib/utils";
import {
  Loader2,
  Newspaper,
  BarChart2,
  Zap,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Brain,
  ShieldCheck,
} from "lucide-react";

// ─── Query keys to invalidate after any research job succeeds ─────────────────
const RESEARCH_INVALIDATION_KEYS = [
  ["news-signals"],
  ["news-outcomes"],
  ["news-summary"],
  ["intelligence-snapshot"],
  ["intelligence-briefing"],
  ["shadow-performance"],
  ["intelligence-graduation"],
] as const;

const RESEARCH_JOB_TYPES = ["NEWS_RESEARCH_CYCLE", "STRATEGY_REPORT", "SHADOW_ANALYSIS"];

// ─── Hook: poll a single job and call onComplete when it reaches a terminal state ──
export function useResearchJobPoll(
  jobId: string | null,
  onComplete: (job: Job) => void,
) {
  const prevStatus = useRef<string | null>(null);

  const query = useQuery({
    queryKey: ["research-job-poll", jobId],
    queryFn: () => apiClient.get<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const s = q.state?.data?.status;
      return s === "QUEUED" || s === "RUNNING" ? 2000 : false;
    },
  });

  useEffect(() => {
    const status = query.data?.status;
    if (!status || !jobId) return;
    const terminal = ["SUCCEEDED", "SUCCEEDED_WITH_WARNINGS", "FAILED", "CANCELLED"];
    if (terminal.includes(status) && prevStatus.current !== status) {
      prevStatus.current = status;
      onComplete(query.data!);
    }
  }, [query.data?.status, jobId, onComplete]);

  return query;
}

// ─── Shared FormError component ───────────────────────────────────────────────
function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 px-3 py-2 rounded-md">
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  );
}

// ─── Shared JobStatusRow ──────────────────────────────────────────────────────
function JobRow({ job }: { job: Job }) {
  return (
    <div className="px-4 py-3 flex items-center justify-between hover:bg-muted/30 transition-colors">
      <div className="flex items-center gap-3">
        <StatusBadge status={job.status} className="shrink-0" />
        <div>
          <p className="text-sm font-medium">{job.job_type.replace(/_/g, " ")}</p>
          <p className="text-[11px] font-mono text-muted-foreground">
            {job.job_id.slice(0, 8)}… · {formatDate(job.started_at || job.created_at)}
          </p>
        </div>
      </div>
      <div className="text-right shrink-0 ml-4">
        {job.duration_seconds != null && (
          <p className="text-xs font-mono text-muted-foreground">
            {job.duration_seconds.toFixed(1)}s
          </p>
        )}
        {job.error_summary && (
          <p className="text-[11px] text-destructive truncate max-w-[160px]">{job.error_summary}</p>
        )}
      </div>
    </div>
  );
}

// ─── News Research Form ────────────────────────────────────────────────────────
function NewsResearchForm({
  onStarted,
}: {
  onStarted: (id: string) => void;
}) {
  const queryClient = useQueryClient();
  const [provider, setProvider] = useState("TWELVE_DATA");
  const [inputType, setInputType] = useState<"symbols" | "watchlist">("symbols");
  const [inputValue, setInputValue] = useState("");
  const [maxRequests, setMaxRequests] = useState("5");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.post<{ job_id: string }>("/jobs/news-research", data),
    onSuccess: (data) => {
      onStarted(data.job_id);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setInputValue("");
      setMaxRequests("5");
      setFormError(null);
      setSubmitted(false);
    },
    onError: (err: Error) => {
      setFormError(err.message);
    },
  });

  const symbolsEmpty =
    inputType === "symbols" &&
    !inputValue
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean).length;

  const canSubmit = !mutation.isPending && !symbolsEmpty;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setFormError(null);

    if (symbolsEmpty) {
      setFormError("Enter at least one symbol (e.g. AAPL, MSFT).");
      return;
    }

    const payload: Record<string, unknown> = {
      provider: provider.toUpperCase(),
      max_price_requests: parseInt(maxRequests, 10) || 5,
    };

    if (inputType === "symbols") {
      payload.symbols = inputValue
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    } else {
      payload.watchlist =
        inputValue.trim() || "data/watchlists/us_large_cap.txt";
    }

    mutation.mutate(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Provider */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground uppercase tracking-wider">
          Provider
        </Label>
        <Select value={provider} onValueChange={setProvider}>
          <SelectTrigger data-testid="select-provider">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="TWELVE_DATA">Twelve Data</SelectItem>
            <SelectItem value="ALPHA_VANTAGE">Alpha Vantage</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Source: mutually exclusive */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground uppercase tracking-wider">
          Source
        </Label>
        <div className="flex gap-2">
          {(["symbols", "watchlist"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => {
                setInputType(t);
                setInputValue("");
                setFormError(null);
              }}
              className={cn(
                "flex-1 py-1.5 rounded border text-xs font-semibold uppercase tracking-wide transition-colors",
                inputType === t
                  ? "bg-primary text-primary-foreground border-primary"
                  : "text-muted-foreground border-border hover:border-muted-foreground/50",
              )}
            >
              {t === "symbols" ? "Symbols" : "Watchlist"}
            </button>
          ))}
        </div>
      </div>

      {/* Source input */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground uppercase tracking-wider">
          {inputType === "symbols" ? "Symbols (comma-separated)" : "Watchlist path"}
        </Label>
        <Input
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            if (formError) setFormError(null);
          }}
          placeholder={
            inputType === "symbols"
              ? "AAPL, MSFT, TSLA"
              : "data/watchlists/us_large_cap.txt"
          }
          data-testid="input-target"
          className={cn(
            submitted && symbolsEmpty && "border-destructive focus-visible:ring-destructive",
          )}
        />
        {inputType === "watchlist" && !inputValue && (
          <p className="text-[11px] text-muted-foreground">
            Defaults to{" "}
            <span className="font-mono">data/watchlists/us_large_cap.txt</span>
          </p>
        )}
      </div>

      {/* Max price requests */}
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground uppercase tracking-wider">
          Max Price Requests
        </Label>
        <Input
          type="number"
          value={maxRequests}
          onChange={(e) => setMaxRequests(e.target.value)}
          min="0"
          data-testid="input-max-requests"
        />
      </div>

      <FormError message={formError} />

      <Button
        type="submit"
        disabled={!canSubmit}
        className="w-full"
        data-testid="submit-news-research"
      >
        {mutation.isPending ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Starting…
          </>
        ) : (
          "Start News Research"
        )}
      </Button>
    </form>
  );
}

// ─── Strategy Report Form ─────────────────────────────────────────────────────
function StrategyReportForm({ onStarted }: { onStarted: (id: string) => void }) {
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      apiClient.post<{ job_id: string }>("/jobs/strategy-report", { force: false }),
    onSuccess: (data) => {
      onStarted(data.job_id);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setFormError(null);
    },
    onError: (err: Error) => setFormError(err.message),
  });

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Evaluates the current strategy rules against recent data and produces a{" "}
        <span className="font-semibold text-foreground">PROMISING</span> or{" "}
        <span className="font-semibold text-foreground">REJECTED</span> verdict.
      </p>
      <FormError message={formError} />
      <Button
        onClick={() => { setFormError(null); mutation.mutate(); }}
        disabled={mutation.isPending}
        className="w-full"
        data-testid="submit-generate-report"
      >
        {mutation.isPending ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Starting…
          </>
        ) : (
          "Generate Strategy Report"
        )}
      </Button>
    </div>
  );
}

// ─── Shadow Analysis Form ─────────────────────────────────────────────────────
function ShadowAnalysisForm({ onStarted }: { onStarted: (id: string) => void }) {
  const queryClient = useQueryClient();
  const [symbolsInput, setSymbolsInput] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.post<{ job_id: string }>("/jobs/shadow-analysis", data),
    onSuccess: (data) => {
      onStarted(data.job_id);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setSymbolsInput("");
      setFormError(null);
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    const symbols = symbolsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const payload: Record<string, unknown> = { force: false };
    if (symbols.length) payload.symbols = symbols;
    mutation.mutate(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Replays shadow-trading decisions against current signal data to measure
        AI performance. Leave symbols empty to run across all configured symbols.
      </p>
      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground uppercase tracking-wider">
          Symbols (optional, comma-separated)
        </Label>
        <Input
          value={symbolsInput}
          onChange={(e) => setSymbolsInput(e.target.value)}
          placeholder="AAPL, MSFT, TSLA — or leave empty for all"
        />
      </div>
      <FormError message={formError} />
      <Button
        type="submit"
        disabled={mutation.isPending}
        className="w-full"
        data-testid="submit-shadow-analysis"
      >
        {mutation.isPending ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Starting…
          </>
        ) : (
          "Run Shadow Analysis"
        )}
      </Button>
    </form>
  );
}

// ─── Intelligence Cycle Card ──────────────────────────────────────────────────

const IC_INVALIDATION_KEYS = [
  ...RESEARCH_INVALIDATION_KEYS,
  ["run-history"] as const,
  ["schedules"] as const,
] as const;

function IntelligenceCycleCard({ onStarted }: { onStarted: (id: string) => void }) {
  const queryClient = useQueryClient();
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => apiClient.post<{ job_id: string }>("/jobs/intelligence-cycle", {}),
    onSuccess: (data) => {
      setLastJobId(data.job_id);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      onStarted(data.job_id);
    },
    onError: (err: Error) => {
      setError(err.message ?? "Failed to queue Intelligence Cycle.");
    },
  });

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-primary" />
          <CardTitle className="text-sm font-bold uppercase tracking-wider">
            Intelligence Cycle
          </CardTitle>
        </div>
        <CardDescription className="text-xs">
          Run the full pipeline: news research, price capture, shadow analysis,
          performance, graduation check, and intelligence snapshot.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Safety badge */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-emerald-500/10 border border-emerald-500/20">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span className="text-xs font-semibold text-emerald-400">
            Trading impact: NONE — Research only
          </span>
        </div>

        {/* Last queued job ID */}
        {lastJobId && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span>
              Queued:{" "}
              <span className="font-mono" data-testid="ic-queued-job-id">
                {lastJobId}
              </span>
            </span>
          </div>
        )}

        {error && (
          <p className="text-xs text-destructive flex items-start gap-1">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            {error}
          </p>
        )}

        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-full"
          data-testid="submit-intelligence-cycle"
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Starting…
            </>
          ) : (
            "Run Intelligence Cycle"
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ResearchPage() {
  const queryClient = useQueryClient();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // When a research job reaches a terminal state, invalidate all related queries
  const handleJobComplete = (job: Job) => {
    setActiveJobId(null);
    if (job.status === "SUCCEEDED" || job.status === "SUCCEEDED_WITH_WARNINGS") {
      RESEARCH_INVALIDATION_KEYS.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: [...key] });
      });
    }
  };

  // Poll the active job
  const { data: activeJobData } = useResearchJobPoll(activeJobId, handleJobComplete);

  // Latest strategy report
  const { data: reportResp } = useQuery({
    queryKey: ["research-report"],
    queryFn: () => apiClient.get<ResearchReportResponse>("/research/latest"),
    refetchInterval: 30_000,
  });
  const report =
    reportResp?.available ? (reportResp.report as Record<string, unknown>) : null;

  // All jobs (for the jobs section below)
  const { data: jobsResp } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => apiClient.get<ListResponse<Job>>("/jobs"),
    refetchInterval: (q) => {
      const hasActive = (q.state.data?.items ?? []).some(
        (j) => j.status === "QUEUED" || j.status === "RUNNING",
      );
      return hasActive ? 2000 : 5000;
    },
  });

  const allJobs = jobsResp?.items ?? [];
  const researchJobs = allJobs.filter((j) => RESEARCH_JOB_TYPES.includes(j.job_type));
  const activeJobs = researchJobs.filter((j) =>
    ["QUEUED", "RUNNING"].includes(j.status),
  );
  const recentJobs = researchJobs
    .filter((j) =>
      ["SUCCEEDED", "SUCCEEDED_WITH_WARNINGS", "FAILED", "CANCELLED"].includes(j.status),
    )
    .slice(0, 10);

  const handleJobStarted = (id: string) => {
    setActiveJobId(id);
    queryClient.invalidateQueries({ queryKey: ["jobs"] });
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 max-w-7xl">
      <h2 className="text-sm font-semibold uppercase tracking-wider">
        Research Operations
      </h2>

      {/* ── Active job banner ─────────────────────────────────────────────── */}
      {activeJobId && activeJobData && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-primary/10 border border-primary/20">
          <Loader2 className="w-4 h-4 animate-spin text-primary shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-primary">
              {activeJobData.job_type.replace(/_/g, " ")} running…
            </p>
            <p className="text-[11px] font-mono text-muted-foreground">
              {activeJobId.slice(0, 8)}…
            </p>
          </div>
          <StatusBadge status={activeJobData.status} className="shrink-0" />
        </div>
      )}

      {/* ── Workflow cards ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* News Research */}
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Newspaper className="w-4 h-4 text-primary" />
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                News Research
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Fetch news and run AI sentiment analysis for one or more symbols.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <NewsResearchForm onStarted={handleJobStarted} />
          </CardContent>
        </Card>

        {/* Strategy Report */}
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-primary" />
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Strategy Report
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Evaluate strategy rules against recent data — produces a
              PROMISING or REJECTED verdict.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StrategyReportForm onStarted={handleJobStarted} />
          </CardContent>
        </Card>

        {/* Shadow Analysis */}
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-primary" />
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Shadow Analysis
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Replay shadow decisions against current signals to measure AI
              trading performance.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ShadowAnalysisForm onStarted={handleJobStarted} />
          </CardContent>
        </Card>

        {/* Intelligence Cycle */}
        <IntelligenceCycleCard onStarted={handleJobStarted} />
      </div>

      {/* ── Latest Strategy Report ───────────────────────────────────────── */}
      {(reportResp !== undefined) && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
            Latest Strategy Report
          </p>
          <Card>
            <CardContent className="pt-6">
              {report ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
                    <span className="font-medium text-sm">Verdict</span>
                    <StatusBadge
                      status={String(report.verdict ?? "UNKNOWN")}
                      className="text-sm px-3 py-1"
                    />
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {report.net_return != null && (
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Net Return</p>
                        <p className="text-lg font-mono">{formatGBP(report.net_return as number)}</p>
                      </div>
                    )}
                    {report.completed_trades != null && (
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Completed Trades</p>
                        <p className="text-lg font-mono">{String(report.completed_trades)}</p>
                      </div>
                    )}
                  </div>
                  {!!report.monte_carlo && (
                    <div className="pt-2 border-t">
                      <p className="text-xs text-muted-foreground uppercase mb-2">Monte Carlo</p>
                      <pre className="text-xs font-mono bg-muted p-2 rounded overflow-auto max-h-32 text-muted-foreground">
                        {JSON.stringify(report.monte_carlo, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-4 text-center">
                  No strategy report available — run one above.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Active Research Jobs ──────────────────────────────────────────── */}
      {activeJobs.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
            Active Jobs
          </p>
          <Card>
            <div className="divide-y divide-border">
              {activeJobs.map((job) => (
                <JobRow key={job.job_id} job={job} />
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* ── Recent Research Jobs ──────────────────────────────────────────── */}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
          Recent Jobs
        </p>
        <Card>
          {jobsResp === undefined ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : recentJobs.length > 0 ? (
            <div className="divide-y divide-border">
              {recentJobs.map((job) => (
                <JobRow key={job.job_id} job={job} />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground text-sm">
              No recent research jobs
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
