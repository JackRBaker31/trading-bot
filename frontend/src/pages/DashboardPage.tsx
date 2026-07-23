import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { apiClient } from "@/lib/api-client";
import {
  AppStatus,
  ListResponse,
  PagedResponse,
  RunHistoryRecord,
  Portfolio,
  Position,
  Order,
  ReconciliationStatus,
  RiskStatus,
  IntelligenceBriefing,
  BriefingAction,
  IntelligenceSnapshot,
  GraduationStatus,
  ShadowPerformanceReport,
  TopOpportunityObject,
  TopOpportunity,
  InfrastructureStatusResponse,
  InfrastructureServiceStatus,
  JobWorkerMetadata,
  ScheduledTask,
  SchedulerMetadata,
  SupervisorMetadata,
} from "@/lib/types";
import { formatCountdown } from "@/lib/schedule-utils";
import { useScheduleList } from "@/hooks/useSchedules";
import { usePositionPrices } from "@/hooks/usePositionPrices";
import { useMarketStatus } from "@/hooks/useMarketStatus";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Progress } from "@/components/ui/progress";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { formatGBP, formatDate } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { useInfrastructureStatus } from "@/hooks/useInfrastructureStatus";
import { usePaperTradingStatus } from "@/hooks/usePaperTradingStatus";
import { useMarketSession } from "@/hooks/useMarketSession";
import {
  CheckCircle2,
  XCircle,
  BrainCircuit,
  TrendingUp,
  ShieldCheck,
  Activity,
  Cpu,
  Server,
  Bot,
  Clock,
  Loader2,
  Power,
  AlertTriangle,
  ChevronDown,
  Play,
  RefreshCw,
  GraduationCap,
  BarChart2,
  Zap,
  CalendarClock,
  Link as LinkIcon,
} from "lucide-react";
import { useLocation, Link } from "wouter";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { RunNewsResearchDialog } from "@/components/RunNewsResearchDialog";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const RUN_TYPE_LABELS: Record<string, string> = {
  NEWS_RESEARCH_CYCLE: "News Research Cycle",
  STRATEGY_REPORT: "Strategy Report Generated",
  PAPER_TRADING_STARTUP: "Paper Trading Started",
  PAPER_TRADING_SHUTDOWN: "Paper Trading Stopped",
  RECONCILIATION: "Reconciliation Run",
  RISK_CHECK: "Risk Check",
};

function labelForRunType(runType: string): string {
  return (
    RUN_TYPE_LABELS[runType] ??
    runType
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

function toTimeStr(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  } catch {
    return "—";
  }
}

function confPct(v: number): string {
  return (v <= 1 ? v * 100 : v).toFixed(0) + "%";
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return (v <= 1 ? v * 100 : v).toFixed(1) + "%";
}

function fmtNum(v: number | null | undefined, decimals = 2): string {
  if (v == null) return "—";
  return v.toFixed(decimals);
}

function outlookColor(outlook: string | null | undefined): string {
  if (!outlook) return "text-muted-foreground";
  const o = outlook.toUpperCase();
  if (["BULLISH", "POSITIVE", "STRONG", "PROMISING"].some((k) => o.includes(k)))
    return "text-emerald-400";
  if (["BEARISH", "NEGATIVE", "WEAK", "CAUTION"].some((k) => o.includes(k)))
    return "text-destructive";
  return "text-amber-400";
}

function outlookBorder(outlook: string | null | undefined): string {
  if (!outlook) return "border-border";
  const o = outlook.toUpperCase();
  if (["BULLISH", "POSITIVE", "STRONG", "PROMISING"].some((k) => o.includes(k)))
    return "border-emerald-500/30";
  if (["BEARISH", "NEGATIVE", "WEAK", "CAUTION"].some((k) => o.includes(k)))
    return "border-destructive/30";
  return "border-amber-500/30";
}

function outlookBg(outlook: string | null | undefined): string {
  if (!outlook) return "";
  const o = outlook.toUpperCase();
  if (["BULLISH", "POSITIVE", "STRONG", "PROMISING"].some((k) => o.includes(k)))
    return "bg-emerald-500/5";
  if (["BEARISH", "NEGATIVE", "WEAK", "CAUTION"].some((k) => o.includes(k)))
    return "bg-destructive/5";
  return "bg-amber-500/5";
}

function readinessColor(r: string | null | undefined): string {
  if (!r) return "text-muted-foreground";
  const s = r.toUpperCase();
  if (s === "READY" || s.includes("READY")) return "text-emerald-400";
  if (s === "BLOCKED" || s.includes("BLOCKED")) return "text-destructive";
  return "text-amber-400";
}

/** Format heartbeat_age_seconds to human-readable relative text. */
function fmtHeartbeatAge(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const s = Math.round(seconds);
  if (s < 60) return `${s} second${s !== 1 ? "s" : ""} ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} minute${m !== 1 ? "s" : ""} ago`;
  return `${Math.floor(m / 60)} hour${Math.floor(m / 60) !== 1 ? "s" : ""} ago`;
}

/** Tailwind class for the online-state indicator dot. */
function infraDotClass(online: boolean): string {
  return online ? "bg-emerald-500" : "bg-destructive";
}

/** Tailwind text class for a service's status label. */
function infraStatusTextClass(status: string, online: boolean): string {
  if (!online) return "text-destructive";
  const s = status.toUpperCase();
  if (["IDLE", "ONLINE", "HEALTHY", "CURRENT", "CONFIGURED"].includes(s)) return "text-emerald-400";
  if (s === "BUSY") return "text-blue-400";
  if (["STALE", "DEGRADED", "WARNING"].includes(s)) return "text-amber-400";
  if (["STOPPED", "NOT_SEEN", "OFFLINE", "FAILED"].includes(s)) return "text-destructive";
  return "text-emerald-400"; // online + unknown status → assume healthy
}

/** CSS classes for the overall_status summary badge. */
function overallStatusClasses(status: string): string {
  const s = status.toUpperCase();
  if (s === "HEALTHY") return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  if (s === "DEGRADED") return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
  return "bg-destructive/10 text-destructive border border-destructive/20";
}

/**
 * Dot colour for Platform Supervisor.
 * Derives colour from status, NOT online flag — FAILED must never appear green.
 */
function supervisorDotClass(status: string): string {
  const s = status.toUpperCase();
  if (s === "RUNNING") return "bg-emerald-500";
  if (s === "DEGRADED" || s === "STALE") return "bg-amber-400";
  return "bg-destructive"; // FAILED, STOPPED, NOT_SEEN, unknown
}

/** Text colour for Platform Supervisor status badge. */
function supervisorStatusTextClass(status: string): string {
  const s = status.toUpperCase();
  if (s === "RUNNING") return "text-emerald-400";
  if (s === "DEGRADED" || s === "STALE") return "text-amber-400";
  return "text-destructive"; // FAILED, STOPPED, NOT_SEEN, unknown
}

/**
 * Returns the operating guidance to show below an offline child service
 * when the Supervisor is active (so we don't tell users to manually launch
 * a duplicate process while the Supervisor owns that service).
 */
function childServiceGuidance(supervisorStatus: string | undefined): "managing" | "failed" | "start_supervisor" {
  if (!supervisorStatus) return "start_supervisor";
  const s = supervisorStatus.toUpperCase();
  if (s === "RUNNING") return "managing";
  if (s === "FAILED") return "failed";
  return "start_supervisor"; // STOPPED, NOT_SEEN, STALE, DEGRADED → prompt supervisor start
}

/**
 * The backend may return `briefing.top_opportunity` as a plain string ticker
 * label OR as a rich object. Extract a displayable string safely either way.
 */
function renderTopOpportunity(val: IntelligenceBriefing["top_opportunity"]): string {
  if (!val) return "";
  if (typeof val === "string") return val;
  // Object shape — prefer symbol/ticker, fall back to headline, then stringify
  const obj = val as TopOpportunityObject;
  return obj.symbol ?? obj.ticker ?? obj.headline ?? "—";
}

/**
 * Reason items inside top_opportunities arrays may be plain strings or objects.
 * Extract a displayable string safely.
 */
function renderReason(item: unknown): string {
  if (!item) return "";
  if (typeof item === "string") return item;
  if (typeof item === "object") {
    const o = item as Record<string, unknown>;
    // Common patterns the backend might use
    return (
      (typeof o.reason === "string" ? o.reason : null) ??
      (typeof o.message === "string" ? o.message : null) ??
      (typeof o.text === "string" ? o.text : null) ??
      (typeof o.headline === "string" ? o.headline : null) ??
      JSON.stringify(item)
    );
  }
  return String(item);
}

// ─── Sub-components ────────────────────────────────────────────────────────────

// ─── Next Scan Countdown ─────────────────────────────────────────────────────

function NextScanCell({ schedulesResp }: { schedulesResp: { items: ScheduledTask[] } | undefined }) {
  const [tick, setTick] = useState(0);
  const schedules = schedulesResp?.items ?? [];

  // Prefer earliest enabled INTELLIGENCE_CYCLE, then any enabled schedule
  const icSchedules = schedules.filter((s) => s.enabled && s.task_type === "INTELLIGENCE_CYCLE" && s.next_run_at);
  const anySchedules = schedules.filter((s) => s.enabled && s.next_run_at);
  const candidates = icSchedules.length > 0 ? icSchedules : anySchedules;
  const target = candidates.length > 0
    ? candidates.reduce((a, b) =>
        new Date(a.next_run_at!).getTime() < new Date(b.next_run_at!).getTime() ? a : b,
      )
    : null;

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  if (!schedulesResp) {
    return (
      <div className="flex items-center gap-2 px-5 py-3 shrink-0">
        <Clock className="w-3.5 h-3.5 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">Next scan</span>
        <span className="text-xs font-mono text-muted-foreground">—</span>
      </div>
    );
  }

  if (!target) {
    return (
      <div className="flex items-center gap-2 px-5 py-3 shrink-0">
        <CalendarClock className="w-3.5 h-3.5 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">Next scan</span>
        <Link href="/schedules" className="text-xs text-primary underline underline-offset-2 hover:no-underline">
          No active schedule
        </Link>
      </div>
    );
  }

  const secsUntil = (new Date(target.next_run_at!).getTime() - Date.now()) / 1000;
  const label = formatCountdown(secsUntil);
  const taskLabel = target.task_type.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="flex items-center gap-2 px-5 py-3 shrink-0" title={`${taskLabel} — ${new Date(target.next_run_at!).toLocaleTimeString()}`}>
      <CalendarClock className="w-3.5 h-3.5 text-muted-foreground" />
      <span className="text-xs text-muted-foreground">Next scan</span>
      <span className={cn("text-xs font-mono font-semibold", secsUntil <= 0 ? "text-amber-400" : "text-foreground")}>
        {label}
      </span>
    </div>
  );
}

function CheckItem({
  label,
  ok,
  reason,
  action,
}: {
  label: string;
  ok: boolean;
  reason?: string;
  action?: string;
}) {
  return (
    <div className="space-y-0.5">
      <div className="flex items-center gap-2 text-sm">
        {ok ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
        ) : (
          <XCircle className="w-3.5 h-3.5 text-destructive shrink-0" />
        )}
        <span className={ok ? "text-foreground" : "text-muted-foreground line-through"}>
          {label}
        </span>
      </div>
      {!ok && reason && (
        <p className="text-[11px] text-amber-400/90 pl-5">{reason}</p>
      )}
      {!ok && action && (
        <p className="text-[11px] text-muted-foreground italic pl-5">→ {action}</p>
      )}
    </div>
  );
}

function InsightChip({
  label,
  value,
  color,
}: {
  label: string;
  value: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="flex flex-col gap-1 p-3 rounded-lg bg-muted/40">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
        {label}
      </span>
      <span className={cn("text-xl font-bold font-mono tabular-nums", color ?? "text-foreground")}>
        {value}
      </span>
    </div>
  );
}

function MetricChip({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <span className={cn("text-sm font-bold", valueClass ?? "text-foreground")}>{value}</span>
    </div>
  );
}

function UnavailableState({
  label,
  onRetry,
}: {
  label: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8 text-center">
      <AlertTriangle className="w-5 h-5 text-muted-foreground" />
      <p className="text-sm text-muted-foreground">{label}</p>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </Button>
      )}
    </div>
  );
}

// ─── Action Card ─────────────────────────────────────────────────────────────

function ActionCard({
  action,
  onRun,
  isPending,
}: {
  action: BriefingAction;
  onRun: () => void;
  isPending: boolean;
}) {
  return (
    <div className="flex-shrink-0 w-52 rounded-xl border border-primary/20 bg-primary/5 p-4 flex flex-col gap-3">
      <div className="flex items-start gap-2">
        <Zap className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
        <p className="text-xs font-semibold text-foreground leading-snug">{action.label}</p>
      </div>
      {action.description && (
        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
          {action.description}
        </p>
      )}
      <Button
        size="sm"
        className="w-full mt-auto"
        onClick={onRun}
        disabled={isPending}
      >
        {isPending ? (
          <>
            <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            Running…
          </>
        ) : (
          <>
            <Play className="w-3.5 h-3.5 mr-1.5" />
            Run
          </>
        )}
      </Button>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const market = useMarketStatus();
  const {
    data: infra,
    isLoading: infraLoading,
    isError: infraError,
    refetch: refetchInfra,
  } = useInfrastructureStatus();
  const { data: ptStatus } = usePaperTradingStatus();
  const marketSession = useMarketSession();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [, navigate] = useLocation();

  // ── Shadow period tab ──────────────────────────────────────────────────────
  const [shadowPeriod, setShadowPeriod] = useState<string>("1d");

  // ── Graduation checklist open/close ───────────────────────────────────────
  const [gradOpen, setGradOpen] = useState(false);

  // ── Action routing state ───────────────────────────────────────────────────
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [newsResearchOpen, setNewsResearchOpen] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<TopOpportunity | null>(null);

  // ─────────────────────────────────────────────────────────────────────────
  // Queries
  // ─────────────────────────────────────────────────────────────────────────

  const startWorkerMutation = useMutation({
    mutationFn: () =>
      apiClient.post("/paper-trading/start", {
        confirm_demo_paper_trading: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["paper-trading-status"] });
      toast({ title: "Paper trading starting", description: "Worker is initializing." });
    },
    onError: (err: any) => {
      toast({ variant: "destructive", title: "Failed to start worker", description: err.message });
    },
  });

  // Used only for known POST actions with explicit payloads (strategy report, shadow analysis).
  // Navigation and modal actions are handled synchronously by handleAction.
  const postMutation = useMutation({
    mutationFn: ({ endpoint, payload }: { endpoint: string; payload: Record<string, unknown> }) =>
      apiClient.post(endpoint.replace(/^\/api/, ""), payload),
    onSuccess: () => {
      setPendingAction(null);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast({ title: "Action queued", description: "Job has been submitted." });
    },
    onError: (err: any) => {
      setPendingAction(null);
      toast({ variant: "destructive", title: "Action failed", description: err.message });
    },
  });

  function handleAction(action: BriefingAction) {
    const type = (action.action_type ?? "").toUpperCase();
    const ep = action.endpoint ?? "";

    // ── Navigation actions ────────────────────────────────────────────────
    if (type === "REVIEW_UNRESOLVED_ORDERS" || ep.includes("/orders")) {
      navigate("/orders");
      return;
    }
    if (type === "RUN_RECONCILIATION" || ep.includes("/reconciliation")) {
      navigate("/reconciliation");
      return;
    }
    if (type === "REVIEW_TOP_OPPORTUNITY" || ep.includes("/research")) {
      navigate("/research");
      return;
    }

    // ── Modal actions ─────────────────────────────────────────────────────
    if (type === "RUN_NEWS_RESEARCH" || ep.includes("/jobs/news-research")) {
      setNewsResearchOpen(true);
      return;
    }
    if (type === "START_PAPER_TRADING" || ep.includes("/paper-trading/start")) {
      startWorkerMutation.mutate();
      return;
    }

    // ── POST actions with known explicit payloads ──────────────────────────
    if (type === "RUN_STRATEGY_REPORT" || ep.includes("/jobs/strategy-report")) {
      setPendingAction(action.label);
      postMutation.mutate({ endpoint: ep, payload: { force: false } });
      return;
    }
    if (type === "RUN_SHADOW_ANALYSIS" || ep.includes("/jobs/shadow-analysis")) {
      setPendingAction(action.label);
      postMutation.mutate({ endpoint: ep, payload: { force: false } });
      return;
    }

    // ── GET actions — safe to execute directly ────────────────────────────
    if (action.method?.toUpperCase() === "GET") {
      setPendingAction(action.label);
      apiClient
        .get(ep.replace(/^\/api/, ""))
        .then(() => {
          setPendingAction(null);
          toast({ title: "Action completed", description: action.label });
        })
        .catch((err: any) => {
          setPendingAction(null);
          toast({ variant: "destructive", title: "Action failed", description: err.message });
        });
      return;
    }

    // ── Unknown POST — never send {}; warn the user ────────────────────────
    toast({
      title: "Manual action required",
      description: `"${action.label}" requires additional input. Please navigate to the relevant page to run it.`,
    });
  }

  const { data: status } = useQuery({
    queryKey: ["api-status"],
    queryFn: () => apiClient.get<AppStatus>("/status"),
    refetchInterval: 30000,
  });

  const {
    data: briefing,
    isLoading: briefingLoading,
    isError: briefingError,
    refetch: refetchBriefing,
  } = useQuery({
    queryKey: ["intelligence-briefing"],
    queryFn: () => apiClient.get<IntelligenceBriefing>("/intelligence/briefing"),
    refetchInterval: 60000,
    retry: 1,
  });

  const {
    data: snapshot,
    isLoading: snapshotLoading,
    isError: snapshotError,
    refetch: refetchSnapshot,
  } = useQuery({
    queryKey: ["intelligence-snapshot"],
    queryFn: () => apiClient.get<IntelligenceSnapshot>("/intelligence/snapshot"),
    refetchInterval: 60000,
    retry: 1,
  });

  const {
    data: graduation,
    isLoading: gradLoading,
    isError: gradError,
    refetch: refetchGrad,
  } = useQuery({
    queryKey: ["intelligence-graduation"],
    queryFn: () => apiClient.get<GraduationStatus>("/intelligence/graduation-status"),
    refetchInterval: 60000,
    retry: 1,
  });

  const {
    data: shadowPerf,
    isLoading: shadowLoading,
    isError: shadowError,
    refetch: refetchShadow,
  } = useQuery({
    queryKey: ["shadow-performance"],
    queryFn: () => apiClient.get<ShadowPerformanceReport>("/shadow-performance"),
    refetchInterval: 60000,
    retry: 1,
  });

  const { data: runHistoryResp } = useQuery({
    queryKey: ["run-history"],
    queryFn: () => apiClient.get<ListResponse<RunHistoryRecord>>("/run-history"),
    refetchInterval: 30000,
  });

  const { data: portfolio } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => apiClient.get<Portfolio>("/portfolio"),
    refetchInterval: 30000,
  });

  const { data: positionsResp } = useQuery({
    queryKey: ["positions"],
    queryFn: () => apiClient.get<{ count: number; items: Position[] }>("/positions"),
    refetchInterval: 30000,
  });

  const { data: unresolvedResp } = useQuery({
    queryKey: ["orders-unresolved"],
    queryFn: () => apiClient.get<PagedResponse<Order>>("/orders/unresolved"),
    refetchInterval: 30000,
  });

  const { data: reconciliation } = useQuery({
    queryKey: ["reconciliation-latest"],
    queryFn: () => apiClient.get<ReconciliationStatus>("/reconciliation/latest"),
    refetchInterval: 30000,
  });

  const { data: riskStatus } = useQuery({
    queryKey: ["risk-status"],
    queryFn: () => apiClient.get<RiskStatus>("/risk/status"),
    refetchInterval: 60000,
  });

  // ── Position prices ──────────────────────────────────────────────────────
  const positions = positionsResp?.items ?? [];
  const positionSymbols = positions.map((p) => p.symbol);
  const { data: priceMap = {} } = usePositionPrices(positionSymbols, 30000);

  const positionMarketValue = positions.reduce((sum, p) => {
    const price = priceMap[p.symbol];
    return price !== undefined ? sum + p.quantity * price : sum;
  }, 0);
  const allPositionsPriced =
    positions.length === 0 || positions.every((p) => priceMap[p.symbol] !== undefined);
  const anyPositionPriced =
    positions.length === 0 || positions.some((p) => priceMap[p.symbol] !== undefined);

  const cash = portfolio?.cash ?? null;
  const startingCash = portfolio?.starting_cash ?? null;
  const totalPortfolioValue = cash !== null ? cash + positionMarketValue : null;

  const plApprox =
    cash !== null && startingCash !== null ? cash - startingCash : null;
  const exposurePct =
    cash !== null && startingCash !== null && startingCash > 0
      ? Math.round(((startingCash - cash) / startingCash) * 100)
      : null;

  // ── Run history ─────────────────────────────────────────────────────────
  const runHistory = runHistoryResp?.items ?? [];
  const lastResearchRun = runHistory.find((r) => r.run_type === "NEWS_RESEARCH_CYCLE");
  const lastStrategyRun = runHistory.find((r) => r.run_type === "STRATEGY_REPORT");

  // ── Schedule list (for Next Scan countdown) ──────────────────────────────
  const { data: schedulesResp } = useScheduleList();

  // ── Infrastructure-backed service health ──────────────────────────────────
  // workerOk / brokerOk are used by the readiness checks below; derived from
  // the authoritative infrastructure status, not inferred in the frontend.
  const workerOk = infra?.services?.job_worker?.online ?? false;
  const brokerOk = infra?.services?.broker?.online ?? false;

  // ── Supervisor state (used by operating guidance) ─────────────────────────
  const supervisorSvc = infra?.services?.supervisor;
  const supervisorStatus = supervisorSvc?.status?.toUpperCase();

  // ── Trading readiness ────────────────────────────────────────────────────
  const workerGuidance = childServiceGuidance(supervisorStatus);
  const readinessChecks = [
    {
      label: "Broker Configured",
      ok: brokerOk,
      reason: "Broker is not configured or not reachable.",
      action: "Check broker configuration on the Risk & Reconciliation page.",
    },
    {
      label: "Job Worker Running",
      ok: workerOk,
      reason: "The background job worker process is not running.",
      action:
        workerGuidance === "managing"
          ? "The KAIRO supervisor is managing this service. Automatic recovery may be in progress."
          : workerGuidance === "failed"
            ? "Automatic recovery has stopped after repeated failures. Manual review is required on the host."
            : "Start the KAIRO platform supervisor on the host: python -m app.run_process_supervisor",
    },
    {
      label: "Portfolio Available",
      ok: !!(portfolio?.available),
      reason: "Portfolio data is not yet available.",
      action: "Check broker connection on the Paper Trading page.",
    },
    {
      label: "Execution Permission Confirmed",
      ok: !!(riskStatus?.execution_permission_confirmed),
      reason: "Execution permission has not been confirmed.",
      action: "Review DEMO paper-trading configuration on the Paper Trading page.",
    },
    {
      label: "Reconciliation Passed",
      ok: !!(reconciliation?.safe_to_start),
      reason: "Reconciliation has not passed — there may be unresolved orders.",
      action: "Review unresolved orders on the Orders page.",
    },
    {
      label: "AI Research Present",
      ok: !!(status?.research_report_exists),
      reason: "No AI research report is available.",
      action: "Run a News Research job from the Research page.",
    },
  ];
  const firstFail = readinessChecks.find((c) => !c.ok);
  const isReady = !firstFail;

  // ── Risk level ───────────────────────────────────────────────────────────
  function riskLevel(ratio: number | undefined): { label: string; color: string } {
    if (ratio === undefined) return { label: "—", color: "text-muted-foreground" };
    if (ratio <= 0.25) return { label: "LOW", color: "text-emerald-400" };
    if (ratio <= 0.5) return { label: "MEDIUM", color: "text-amber-400" };
    return { label: "HIGH", color: "text-destructive" };
  }
  const risk = riskLevel(riskStatus?.max_portfolio_exposure_ratio);

  // ── Shadow period resolution ─────────────────────────────────────────────
  const shadowPeriods = Object.keys(shadowPerf?.periods ?? {});
  const PERIOD_LABELS: Record<string, string> = { "1h": "1H", "1d": "1D", "5d": "5D" };
  const activePeriodKey =
    shadowPeriods.find((k) => k.toLowerCase() === shadowPeriod.toLowerCase()) ??
    shadowPeriods[0] ??
    "1d";
  const activePeriodStats = shadowPerf?.periods?.[activePeriodKey] ?? null;

  // Build chart data for the active period
  const shadowChartData = activePeriodStats
    ? [
        { name: "Dir. Success", value: activePeriodStats.directional_success != null ? +(activePeriodStats.directional_success * 100).toFixed(1) : null, fill: "#10b981" },
        { name: "Profitable", value: activePeriodStats.profitable_after_costs != null ? +(activePeriodStats.profitable_after_costs * 100).toFixed(1) : null, fill: "#6366f1" },
        { name: "Avg Return", value: activePeriodStats.average_return != null ? +(activePeriodStats.average_return * 100).toFixed(2) : null, fill: "#D4AF37" },
        { name: "Stability", value: activePeriodStats.rolling_stability != null ? +(activePeriodStats.rolling_stability * 100).toFixed(1) : null, fill: "#38bdf8" },
        { name: "Coverage", value: activePeriodStats.coverage != null ? +(activePeriodStats.coverage * 100).toFixed(1) : null, fill: "#a78bfa" },
      ].filter((d) => d.value != null)
    : [];

  // ── Graduation progress ──────────────────────────────────────────────────
  const gradTotal = graduation
    ? (graduation.checks_passed ?? 0) + (graduation.checks_remaining ?? 0)
    : 0;
  const gradPct = gradTotal > 0 ? Math.round(((graduation?.checks_passed ?? 0) / gradTotal) * 100) : 0;

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4 w-full">

      {/* ── 1. AI Briefing Hero ──────────────────────────────────────────────── */}
      <Card
        className={cn(
          "border",
          briefing?.market_outlook
            ? cn(outlookBorder(briefing.market_outlook), outlookBg(briefing.market_outlook))
            : "border-primary/20 bg-primary/5",
        )}
      >
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-center gap-2 mb-5">
            <BrainCircuit className="w-4 h-4 text-primary shrink-0" />
            <span className="text-[11px] font-bold uppercase tracking-widest text-primary/70">
              AI Daily Briefing
            </span>
            {briefing?.generated_at && (
              <span className="ml-auto text-[10px] text-muted-foreground font-mono">
                {timeAgo(briefing.generated_at)}
              </span>
            )}
          </div>

          {briefingLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-8 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
                {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-12" />)}
              </div>
            </div>
          ) : briefingError ? (
            <UnavailableState
              label="AI Briefing unavailable — backend not responding."
              onRetry={() => refetchBriefing()}
            />
          ) : briefing ? (
            <div className="space-y-5">
              {/* Headline */}
              {briefing.headline && (
                <div>
                  <h2 className="text-2xl font-black leading-tight text-foreground">
                    {briefing.headline}
                  </h2>
                  {briefing.summary && (
                    <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
                      {briefing.summary}
                    </p>
                  )}
                </div>
              )}

              {/* Metric chips */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {briefing.market_outlook && (
                  <MetricChip
                    label="Market Outlook"
                    value={briefing.market_outlook}
                    valueClass={cn("font-black text-base", outlookColor(briefing.market_outlook))}
                  />
                )}
                {briefing.confidence != null && (
                  <MetricChip
                    label="Confidence"
                    value={confPct(briefing.confidence)}
                  />
                )}
                {briefing.trading_readiness && (
                  <MetricChip
                    label="Trading Readiness"
                    value={briefing.trading_readiness}
                    valueClass={cn("text-sm", readinessColor(briefing.trading_readiness))}
                  />
                )}
                {briefing.evidence_quality && (
                  <MetricChip label="Evidence Quality" value={briefing.evidence_quality} />
                )}
                {briefing.graduation_status && (
                  <MetricChip label="Graduation Status" value={briefing.graduation_status} />
                )}
                {briefing.top_opportunity && (
                  <MetricChip
                    label="Top Opportunity"
                    value={renderTopOpportunity(briefing.top_opportunity)}
                    valueClass="font-black font-mono text-primary"
                  />
                )}
              </div>

              {/* Warnings */}
              {Array.isArray(briefing.warnings) && briefing.warnings.length > 0 && (
                <div className="space-y-1.5">
                  {briefing.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2"
                    >
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <UnavailableState label="No briefing data available yet." onRetry={() => refetchBriefing()} />
          )}
        </CardContent>
      </Card>

      {/* ── 2. Recommended Action Cards ──────────────────────────────────────── */}
      {briefing && Array.isArray(briefing.actions) && briefing.actions.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" />
            Recommended Actions
          </p>
          <div className="flex gap-3 overflow-x-auto pb-1">
            {briefing.actions.map((action, i) => (
              <ActionCard
                key={i}
                action={action}
                isPending={pendingAction === action.label && postMutation.isPending}
                onRun={() => handleAction(action)}
              />
            ))}
          </div>
        </div>
      )}

      {/* News Research dialog — opened by the RUN_NEWS_RESEARCH action card */}
      <RunNewsResearchDialog
        open={newsResearchOpen}
        onOpenChange={setNewsResearchOpen}
        onStarted={(id) => {
          toast({ title: "News research started", description: `Job ${id} queued.` });
          queryClient.invalidateQueries({ queryKey: ["jobs"] });
        }}
      />

      {/* ── 3. Market Status Strip ──────────────────────────────────────────── */}
      <div className="flex items-center gap-0 rounded-xl border border-border bg-card overflow-x-auto divide-x divide-border text-sm">
        <div className="flex items-center gap-3 px-5 py-3 shrink-0">
          <div
            className={cn(
              "w-2 h-2 rounded-full shrink-0",
              market.isOpen ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground",
            )}
          />
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mr-2">
              NYSE
            </span>
            <span
              className={cn(
                "font-bold text-xs uppercase tracking-wide",
                market.isOpen ? "text-emerald-400" : "text-muted-foreground",
              )}
            >
              {market.isOpen ? "Open" : "Closed"}
            </span>
          </div>
          <span className="text-xs text-muted-foreground">{market.countdown}</span>
        </div>
        <NextScanCell schedulesResp={schedulesResp} />
        <div className="flex items-center gap-2 px-5 py-3 shrink-0">
          <BrainCircuit className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Last AI research</span>
          <span className="text-xs font-mono font-semibold text-foreground">
            {runHistoryResp ? toTimeStr(lastResearchRun?.started_at) : "—"}
          </span>
        </div>
        <div className="flex items-center gap-2 px-5 py-3 shrink-0">
          <Activity className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Last strategy report</span>
          <span className="text-xs font-mono font-semibold text-foreground">
            {runHistoryResp ? toTimeStr(lastStrategyRun?.started_at) : "—"}
          </span>
        </div>
      </div>

      {/* ── 4. System Health ──────────────────────────────────────────────────── */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
            <Server className="w-3.5 h-3.5" />
            System Health
            {infra && (
              <span className={cn("ml-auto text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-md", overallStatusClasses(infra.overall_status))}>
                {infra.overall_status}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {infraLoading && !infra ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : infraError && !infra ? (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <AlertTriangle className="w-7 h-7 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Infrastructure status unavailable</p>
              <Button size="sm" variant="outline" onClick={() => refetchInfra()}>
                <RefreshCw className="w-3.5 h-3.5 mr-2" /> Retry
              </Button>
            </div>
          ) : infra ? (
            <div className="divide-y divide-border">
              {/* ── Platform Supervisor — expanded (shown first) ────────────── */}
              {infra.services.supervisor ? (() => {
                const svc = infra.services.supervisor;
                const meta = svc.metadata as unknown as SupervisorMetadata;
                const svStatus = svc.status.toUpperCase();
                const isFailed = svStatus === "FAILED";
                const isStopped = svStatus === "STOPPED" || svStatus === "NOT_SEEN" || svStatus === "STALE";
                const isDegraded = svStatus === "DEGRADED";
                return (
                  <div className="py-2.5 first:pt-0">
                    <div className="flex items-start gap-3">
                      <div className={cn("mt-1 w-2 h-2 rounded-full shrink-0", supervisorDotClass(svc.status))} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-semibold uppercase tracking-wider">
                            Platform Supervisor
                          </span>
                          <span className={cn("text-[10px] font-bold uppercase", supervisorStatusTextClass(svc.status))}>
                            {svc.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">{svc.detail}</p>
                        {/* Operational guidance */}
                        {isFailed && (
                          <p className="text-[11px] text-destructive font-medium mt-0.5">
                            Automatic recovery has stopped after repeated failures. Manual review is required on the host.
                          </p>
                        )}
                        {!isFailed && (isStopped || !svc.online) && (
                          <p className="text-[11px] text-muted-foreground mt-0.5">
                            Start the KAIRO platform supervisor on the host:{" "}
                            <code className="font-mono">python -m app.run_process_supervisor</code>
                          </p>
                        )}
                        {/* Metadata grid */}
                        <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[10px] text-muted-foreground">
                          {meta.restart_enabled === true && (
                            <span className="text-emerald-400">Automatic recovery enabled</span>
                          )}
                          {meta.restart_enabled === false && (
                            <span className="text-amber-400">Automatic recovery disabled</span>
                          )}
                          {typeof meta.managed_process_count === "number" && (
                            <span>{meta.managed_process_count} services managed</span>
                          )}
                          {typeof meta.healthy_process_count === "number" && (
                            <span className={
                              meta.healthy_process_count === meta.managed_process_count
                                ? "text-emerald-400"
                                : "text-amber-400"
                            }>
                              {meta.healthy_process_count} healthy
                            </span>
                          )}
                          {typeof meta.recovering_process_count === "number" && meta.recovering_process_count > 0 && (
                            <span className="text-amber-400">
                              {meta.recovering_process_count} recovering
                              {isDegraded && " — Automatic recovery in progress"}
                            </span>
                          )}
                          {typeof meta.failed_process_count === "number" && meta.failed_process_count > 0 && (
                            <span className="text-destructive">
                              {meta.failed_process_count} failed — Manual review required
                            </span>
                          )}
                          {typeof meta.process_id === "number" && (
                            <span className="font-mono">PID {meta.process_id}</span>
                          )}
                          {typeof meta.status_age_seconds === "number" && (
                            <span>Status updated {fmtHeartbeatAge(meta.status_age_seconds)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })() : (
                <div className="py-2.5 first:pt-0 flex items-center gap-3">
                  <div className="mt-1 w-2 h-2 rounded-full shrink-0 bg-muted-foreground/40" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-semibold uppercase tracking-wider">Platform Supervisor</span>
                    </div>
                    <p className="text-[11px] text-muted-foreground">Supervisor status unavailable</p>
                  </div>
                </div>
              )}

              {/* ── API, Storage, Broker, Market Data, News ────────────────── */}
              {(["api", "storage", "broker", "market_data", "news"] as const).map((key) => {
                const svc = infra.services[key];
                if (!svc) return null;
                return (
                  <div key={key} className="flex items-start gap-3 py-2.5 first:pt-0">
                    <div className={cn("mt-1 w-2 h-2 rounded-full shrink-0", infraDotClass(svc.online))} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-semibold uppercase tracking-wider">
                          {svc.name.replace(/_/g, " ")}
                        </span>
                        <span className={cn("text-[10px] font-bold uppercase", infraStatusTextClass(svc.status, svc.online))}>
                          {svc.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-snug mt-0.5 truncate" title={svc.detail}>
                        {svc.detail}
                      </p>
                    </div>
                  </div>
                );
              })}

              {/* ── Job Worker — expanded ─────────────────────────────────── */}
              {infra.services.job_worker && (() => {
                const svc = infra.services.job_worker;
                const meta = svc.metadata as unknown as JobWorkerMetadata;
                const isBusy = svc.status.toUpperCase() === "BUSY";
                return (
                  <div className="py-2.5">
                    <div className="flex items-start gap-3">
                      <div
                        className={cn(
                          "mt-1 w-2 h-2 rounded-full shrink-0",
                          infraDotClass(svc.online),
                          isBusy && "animate-pulse",
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-semibold uppercase tracking-wider">
                            Job Worker
                          </span>
                          <span className={cn("text-[10px] font-bold uppercase", infraStatusTextClass(svc.status, svc.online))}>
                            {svc.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">{svc.detail}</p>
                        {!svc.online && (() => {
                          const guidance = childServiceGuidance(supervisorStatus);
                          if (guidance === "managing") return (
                            <p className="text-[11px] text-muted-foreground mt-0.5">
                              The KAIRO supervisor is managing this service.
                              Automatic recovery may be in progress.
                              Review supervisor diagnostics if the service does not recover.
                            </p>
                          );
                          if (guidance === "failed") return (
                            <p className="text-[11px] text-destructive mt-0.5">
                              Automatic recovery has stopped after repeated failures.
                              Manual review is required on the host.
                            </p>
                          );
                          return (
                            <p className="text-[11px] text-muted-foreground mt-0.5">
                              Start the KAIRO platform supervisor on the host:{" "}
                              <code className="font-mono">python -m app.run_process_supervisor</code>
                            </p>
                          );
                        })()}
                        <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[10px] text-muted-foreground">
                          {typeof meta.heartbeat_age_seconds === "number" && (
                            <span>Heartbeat {fmtHeartbeatAge(meta.heartbeat_age_seconds)}</span>
                          )}
                          {typeof meta.jobs_processed === "number" && (
                            <span>{meta.jobs_processed} jobs processed</span>
                          )}
                          {typeof meta.process_id === "number" && (
                            <span className="font-mono">PID {meta.process_id}</span>
                          )}
                          {isBusy && typeof meta.current_job_type === "string" && (
                            <span>Running: <span className="font-mono">{meta.current_job_type.replace(/_/g, " ")}</span></span>
                          )}
                          {isBusy && typeof meta.current_job_id === "string" && (
                            <span className="font-mono" title={meta.current_job_id}>
                              ID: {meta.current_job_id.slice(0, 8)}…
                            </span>
                          )}
                          {typeof meta.last_error === "string" && meta.last_error && (
                            <span className="text-destructive" title={meta.last_error}>
                              Error: {meta.last_error}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* ── Scheduler — expanded ───────────────────────────────────── */}
              {infra.services.scheduler && (() => {
                const svc = infra.services.scheduler;
                const meta = svc.metadata as unknown as SchedulerMetadata;
                const isBusy = svc.status.toUpperCase() === "BUSY";
                return (
                  <div className="py-2.5">
                    <div className="flex items-start gap-3">
                      <div
                        className={cn(
                          "mt-1 w-2 h-2 rounded-full shrink-0",
                          infraDotClass(svc.online),
                          isBusy && "animate-pulse",
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-semibold uppercase tracking-wider">
                            Scheduler
                          </span>
                          <span className={cn("text-[10px] font-bold uppercase", infraStatusTextClass(svc.status, svc.online))}>
                            {svc.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">{svc.detail}</p>
                        {!svc.online && (() => {
                          const guidance = childServiceGuidance(supervisorStatus);
                          if (guidance === "managing") return (
                            <p className="text-[11px] text-muted-foreground mt-0.5">
                              The KAIRO supervisor is managing this service.
                              Automatic recovery may be in progress.
                              Review supervisor diagnostics if the service does not recover.
                            </p>
                          );
                          if (guidance === "failed") return (
                            <p className="text-[11px] text-destructive mt-0.5">
                              Automatic recovery has stopped after repeated failures.
                              Manual review is required on the host.
                            </p>
                          );
                          return (
                            <p className="text-[11px] text-muted-foreground mt-0.5">
                              Start the KAIRO platform supervisor on the host:{" "}
                              <code className="font-mono">python -m app.run_process_supervisor</code>
                            </p>
                          );
                        })()}
                        <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[10px] text-muted-foreground">
                          {typeof meta.heartbeat_age_seconds === "number" && (
                            <span>Heartbeat {fmtHeartbeatAge(meta.heartbeat_age_seconds)}</span>
                          )}
                          {typeof meta.tasks_processed === "number" && (
                            <span>{meta.tasks_processed} tasks processed</span>
                          )}
                          {typeof meta.process_id === "number" && (
                            <span className="font-mono">PID {meta.process_id}</span>
                          )}
                          {isBusy && typeof meta.current_task_type === "string" && (
                            <span>Running: <span className="font-mono">{meta.current_task_type.replace(/_/g, " ")}</span></span>
                          )}
                          {isBusy && typeof meta.current_schedule_id === "string" && (
                            <span className="font-mono">Schedule: {meta.current_schedule_id.slice(0, 8)}…</span>
                          )}
                          {typeof meta.started_at === "string" && meta.started_at && (
                            <span>Since: {formatDate(meta.started_at)}</span>
                          )}
                          {typeof meta.last_error === "string" && meta.last_error && (
                            <span className="text-destructive" title={meta.last_error}>
                              Error: {meta.last_error}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* ── 4b. Platform Operations — compact supervisor summary ──────────────── */}
      {infra && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              Platform Operations
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const sup = infra.services.supervisor;
              if (!sup) {
                return (
                  <p className="text-[11px] text-muted-foreground">
                    Supervisor status unavailable — start{" "}
                    <code className="font-mono">python -m app.run_process_supervisor</code> on the host.
                  </p>
                );
              }
              const meta = sup.metadata as unknown as SupervisorMetadata;
              const svStatus = sup.status.toUpperCase();
              return (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full shrink-0", supervisorDotClass(sup.status))} />
                    <span className="text-[11px] font-medium">
                      Supervisor:{" "}
                      <span className={supervisorStatusTextClass(sup.status)}>
                        {svStatus === "RUNNING" ? "Running" : sup.status}
                      </span>
                    </span>
                  </div>
                  {meta.restart_enabled === true && (
                    <p className="text-[11px] text-muted-foreground pl-4">Automatic recovery: Enabled</p>
                  )}
                  {meta.restart_enabled === false && (
                    <p className="text-[11px] text-amber-400 pl-4">Automatic recovery: Disabled</p>
                  )}
                  {typeof meta.managed_process_count === "number" && typeof meta.healthy_process_count === "number" && (
                    <p className="text-[11px] text-muted-foreground pl-4">
                      Managed services:{" "}
                      <span className={meta.healthy_process_count === meta.managed_process_count ? "text-emerald-400" : "text-amber-400"}>
                        {meta.healthy_process_count}/{meta.managed_process_count} healthy
                      </span>
                    </p>
                  )}
                  {typeof meta.recovering_process_count === "number" && meta.recovering_process_count > 0 && (
                    <p className="text-[11px] text-amber-400 pl-4">
                      {meta.recovering_process_count} service{meta.recovering_process_count !== 1 ? "s" : ""} recovering — Automatic recovery in progress
                    </p>
                  )}
                  {typeof meta.failed_process_count === "number" && meta.failed_process_count > 0 && (
                    <p className="text-[11px] text-destructive pl-4 font-medium">
                      {meta.failed_process_count} service{meta.failed_process_count !== 1 ? "s" : ""} require{meta.failed_process_count === 1 ? "s" : ""} manual review
                    </p>
                  )}
                </div>
              );
            })()}
          </CardContent>
        </Card>
      )}

      {/* ── 4c. Paper Trading + Market & Provider ─────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Paper Trading */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              Paper Trading
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">State</span>
              {ptStatus ? (
                <StatusBadge status={ptStatus.state} />
              ) : (
                <Skeleton className="h-5 w-20" />
              )}
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Process ID</span>
              <span className="font-mono text-xs">
                {ptStatus ? ptStatus.process_id ?? "—" : <Skeleton className="h-4 w-16 inline-block" />}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Stop Requested</span>
              <span className={cn("text-xs font-semibold uppercase", ptStatus?.stop_requested ? "text-amber-400" : "text-muted-foreground")}>
                {ptStatus ? (ptStatus.stop_requested ? "YES" : "NO") : "—"}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Market & Provider */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              Market & Provider
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">{marketSession.exchange}</span>
              <span className={cn("text-sm font-bold uppercase tracking-wide", marketSession.isOpen ? "text-emerald-400" : "text-destructive")}>
                {marketSession.isOpen ? "OPEN" : "CLOSED"}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">{marketSession.label}</p>
            <div className="border-t border-border pt-3 space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Data Provider</span>
                <span className="font-mono text-xs uppercase">
                  {status?.market_data_provider ?? <Skeleton className="h-4 w-20 inline-block" />}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Mode</span>
                <span className="font-mono text-xs uppercase">{status?.application_mode ?? "—"}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Hours Enforced</span>
                <span className={cn("text-xs font-semibold uppercase", status?.market_hours_enforced ? "text-emerald-400" : "text-muted-foreground")}>
                  {status ? (status.market_hours_enforced ? "YES" : "NO") : "—"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── 5. Portfolio + AI Intelligence + Trading Readiness ───────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* Portfolio Summary — 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5" />
              Portfolio Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex items-baseline gap-2 mb-1">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                  Portfolio Value
                </p>
                {portfolio?.available && positions.length > 0 && (
                  <span className="text-[10px] text-muted-foreground">
                    {allPositionsPriced ? "cash + positions" : anyPositionPriced ? "cash + partial" : "cash only"}
                  </span>
                )}
              </div>
              {portfolio ? (
                portfolio.available && cash !== null ? (
                  <p className="text-4xl font-black font-mono tabular-nums">
                    {formatGBP(totalPortfolioValue ?? cash)}
                  </p>
                ) : (
                  <p className="text-2xl font-bold text-muted-foreground">Unavailable</p>
                )
              ) : (
                <Skeleton className="h-10 w-44" />
              )}
            </div>
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Today's P/L</span>
                {portfolio ? (
                  plApprox !== null ? (
                    <span className={cn("text-base font-bold font-mono tabular-nums", plApprox >= 0 ? "text-emerald-400" : "text-destructive")}>
                      {plApprox >= 0 ? "+" : ""}{formatGBP(plApprox)}
                    </span>
                  ) : (
                    <span className="text-base font-bold text-muted-foreground">—</span>
                  )
                ) : (
                  <Skeleton className="h-5 w-20" />
                )}
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Exposure</span>
                {portfolio ? (
                  exposurePct !== null ? (
                    <span className="text-base font-bold font-mono tabular-nums">{exposurePct}%</span>
                  ) : (
                    <span className="text-base font-bold text-muted-foreground">—</span>
                  )
                ) : (
                  <Skeleton className="h-5 w-12" />
                )}
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Cash</span>
                <span className="text-base font-bold font-mono tabular-nums text-accent">
                  {portfolio ? (
                    portfolio.available && cash !== null ? formatGBP(cash) : "—"
                  ) : (
                    <Skeleton className="h-5 w-20 inline-block" />
                  )}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Open Positions</span>
                <span className="text-base font-bold font-mono tabular-nums">
                  {portfolio ? portfolio.position_count : <Skeleton className="h-5 w-8 inline-block" />}
                </span>
              </div>
            </div>
            {portfolio?.available && positions.length > 0 && !allPositionsPriced && (
              <p className="text-[11px] text-muted-foreground border-t border-border pt-2">
                {anyPositionPriced ? "Some position prices unavailable — value understated." : "Position prices unavailable — showing cash only."}
              </p>
            )}
          </CardContent>
        </Card>

        {/* AI Intelligence (snapshot) — 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5" />
              AI Intelligence
            </CardTitle>
          </CardHeader>
          <CardContent>
            {snapshotLoading ? (
              <div className="grid grid-cols-2 gap-2">
                {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-16" />)}
              </div>
            ) : snapshotError ? (
              <UnavailableState label="Intelligence snapshot unavailable." onRetry={() => refetchSnapshot()} />
            ) : snapshot ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <InsightChip label="Total Signals" value={snapshot.total_signals ?? "—"} />
                  <InsightChip label="High Confidence" value={snapshot.high_confidence_signals ?? "—"} color="text-emerald-400" />
                  <InsightChip label="Material Events" value={snapshot.material_events ?? "—"} color="text-amber-400" />
                  <InsightChip label="Actionable" value={snapshot.actionable_signals ?? "—"} color="text-primary" />
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 pt-1">
                  {snapshot.evidence_quality && (
                    <MetricChip label="Evidence Quality" value={snapshot.evidence_quality} />
                  )}
                  {snapshot.research_freshness && (
                    <MetricChip label="Research Freshness" value={timeAgo(snapshot.research_freshness)} />
                  )}
                  {snapshot.risk_warnings && snapshot.risk_warnings.length > 0 && (
                    <div className="col-span-2">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Risk Warnings</p>
                      {snapshot.risk_warnings.slice(0, 2).map((w, i) => (
                        <p key={i} className="text-[11px] text-amber-400 leading-snug">• {w}</p>
                      ))}
                    </div>
                  )}
                </div>
                {/* Top opportunities */}
                {snapshot.top_opportunities && snapshot.top_opportunities.length > 0 && (
                  <div className="border-t border-border pt-3">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">Top Opportunities</p>
                    <div className="space-y-2">
                      {snapshot.top_opportunities.slice(0, 2).map((opp, i) => (
                        <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-muted/30">
                          <div className="shrink-0">
                            <p className="text-sm font-black font-mono text-primary">{opp.ticker}</p>
                            <p className="text-[10px] text-muted-foreground">{opp.classification}</p>
                          </div>
                          <div className="flex-1 min-w-0 space-y-0.5">
                            {opp.score != null && (
                              <p className="text-xs text-muted-foreground">Score: <span className="font-bold text-foreground">{fmtNum(opp.score)}</span></p>
                            )}
                            {opp.confidence != null && (
                              <p className="text-xs text-muted-foreground">Confidence: <span className="font-bold text-foreground">{confPct(opp.confidence)}</span></p>
                            )}
                            {opp.current_status && (
                              <p className="text-[11px] text-muted-foreground truncate">{opp.current_status}</p>
                            )}
                            {opp.blocking_reasons && opp.blocking_reasons.length > 0 && (
                              <p className="text-[11px] text-destructive truncate">⚠ {renderReason(opp.blocking_reasons[0])}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <UnavailableState label="No snapshot available." onRetry={() => refetchSnapshot()} />
            )}
          </CardContent>
        </Card>

        {/* Trading Readiness — 1 col */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              Trading Readiness
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {readinessChecks.map((c) => (
                <CheckItem key={c.label} label={c.label} ok={c.ok} reason={c.reason} action={c.action} />
              ))}
            </div>

            {/* Environment & safety indicators */}
            <div className="space-y-1.5 border-t border-border pt-3">
              {riskStatus?.broker_environment && (
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted-foreground">Broker Environment</span>
                  <span className="font-mono font-semibold uppercase text-foreground">{riskStatus.broker_environment}</span>
                </div>
              )}
              {(unresolvedResp?.total_count ?? 0) > 0 && (
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted-foreground">Unresolved Orders</span>
                  <span className="font-mono font-semibold text-amber-400">{unresolvedResp!.total_count}</span>
                </div>
              )}
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Real-Money Trading</span>
                <span className={cn("font-mono font-semibold uppercase", riskStatus?.real_money_trading_enabled ? "text-destructive" : "text-emerald-400")}>
                  {riskStatus ? (riskStatus.real_money_trading_enabled ? "ENABLED" : "DISABLED") : "—"}
                </span>
              </div>
            </div>

            {ptStatus?.state === "STOPPED" && (
              <Button
                size="sm"
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={() => startWorkerMutation.mutate()}
                disabled={startWorkerMutation.isPending}
                data-testid="dashboard-start-worker"
              >
                {startWorkerMutation.isPending ? (
                  <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Starting…</>
                ) : (
                  <><Power className="w-3.5 h-3.5 mr-2" />Start Worker</>
                )}
              </Button>
            )}
            {(ptStatus?.state === "STARTING" || ptStatus?.state === "STOP_REQUESTED") && !startWorkerMutation.isPending && (
              <Button size="sm" disabled variant="outline" className="w-full">
                <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                {ptStatus.state === "STARTING" ? "Starting…" : "Stopping…"}
              </Button>
            )}
            <div className={cn("p-3 rounded-lg text-center border", isReady ? "bg-emerald-500/10 border-emerald-500/20" : "bg-destructive/10 border-destructive/20")}>
              <p className={cn("text-sm font-bold uppercase tracking-widest", isReady ? "text-emerald-400" : "text-destructive")}>
                {isReady ? "READY" : "NOT READY"}
              </p>
              {!isReady && firstFail && (
                <div className="mt-2 text-left space-y-1">
                  <p className="text-[11px] font-semibold text-destructive">Reason</p>
                  <p className="text-[11px] text-muted-foreground">
                    {firstFail.reason ?? `${firstFail.label} not satisfied`}
                  </p>
                  <p className="text-[11px] font-semibold text-muted-foreground mt-1">Action</p>
                  <p className="text-[11px] text-muted-foreground italic">{firstFail.action}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── 6. Graduation Progress + Shadow Performance ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Graduation Progress */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5" />
              Graduation Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            {gradLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-2 w-full" />
                <div className="space-y-2">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-6" />)}</div>
              </div>
            ) : gradError ? (
              <UnavailableState label="Graduation status unavailable." onRetry={() => refetchGrad()} />
            ) : graduation ? (
              <div className="space-y-4">
                {/* RESEARCH ONLY banner */}
                {(graduation.stage ?? "").toUpperCase().includes("RESEARCH") && (
                  <div className="flex items-center justify-center gap-2 py-1.5 px-3 rounded-md bg-amber-500/10 border border-amber-500/20">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <p className="text-xs font-bold uppercase tracking-widest text-amber-400">Research Only</p>
                  </div>
                )}

                {/* Stage */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">Stage</p>
                    <p className="text-sm font-bold text-foreground">
                      {graduation.stage === "RESEARCH_ONLY"
                        ? "Research Only"
                        : graduation.stage === "ELIGIBLE_FOR_PAPER_FILTER_REVIEW"
                          ? "Eligible For Paper Filter Review"
                          : graduation.stage}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-black text-primary font-mono">{gradPct}%</p>
                    <p className="text-[10px] text-muted-foreground">
                      {graduation.checks_passed ?? 0}/{gradTotal} checks
                    </p>
                  </div>
                </div>

                {/* Progress bar */}
                <Progress value={gradPct} className="h-2" />

                {/* Stats row */}
                <div className="flex gap-4">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    <span className="text-xs text-muted-foreground">{graduation.checks_passed ?? 0} passed</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">{graduation.checks_remaining ?? 0} remaining</span>
                  </div>
                </div>

                {/* Expandable checklist */}
                {Array.isArray(graduation.checks) && graduation.checks.length > 0 && (
                  <Collapsible open={gradOpen} onOpenChange={setGradOpen}>
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" size="sm" className="w-full justify-between text-xs text-muted-foreground hover:text-foreground -mx-1 px-1">
                        <span>{gradOpen ? "Hide" : "Show"} checklist</span>
                        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", gradOpen && "rotate-180")} />
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <div className="space-y-1.5 pt-2 border-t border-border mt-1">
                        {graduation.checks.map((check, i) => (
                          <div key={i} className="flex items-start gap-2">
                            {check.passed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5" />
                            )}
                            <div>
                              <p className={cn("text-xs font-medium", check.passed ? "text-foreground" : "text-muted-foreground line-through")}>
                                {check.name}
                              </p>
                              {check.description && !check.passed && (
                                <p className="text-[11px] text-muted-foreground italic">{check.description}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                )}

                {/* Trading impact */}
                {!!(graduation as Record<string, unknown>).trading_impact && (
                  <div className="border-t border-border pt-3">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Trading Impact</p>
                    <p className="text-xs font-semibold text-foreground">
                      {String((graduation as Record<string, unknown>).trading_impact)}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <UnavailableState label="No graduation data available." onRetry={() => refetchGrad()} />
            )}
          </CardContent>
        </Card>

        {/* Shadow Performance */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <BarChart2 className="w-3.5 h-3.5" />
              Shadow Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            {shadowLoading ? (
              <div className="space-y-4">
                <div className="flex gap-2"><Skeleton className="h-7 w-12" /><Skeleton className="h-7 w-12" /><Skeleton className="h-7 w-12" /></div>
                <div className="grid grid-cols-3 gap-2">{[1,2,3,4,5,6].map((i) => <Skeleton key={i} className="h-14" />)}</div>
                <Skeleton className="h-32 w-full" />
              </div>
            ) : shadowError ? (
              <UnavailableState label="Shadow performance unavailable." onRetry={() => refetchShadow()} />
            ) : shadowPerf && shadowPerf.available ? (
              <div className="space-y-4">
                {/* Period tabs */}
                <div className="flex gap-1.5">
                  {(["1h", "1d", "5d"] as const).map((p) => {
                    const key = shadowPeriods.find((k) => k.toLowerCase() === p) ?? p;
                    const exists = shadowPeriods.some((k) => k.toLowerCase() === p);
                    return (
                      <button
                        key={p}
                        onClick={() => setShadowPeriod(p)}
                        disabled={!exists}
                        className={cn(
                          "px-3 py-1 rounded-md text-xs font-semibold uppercase tracking-wide transition-colors",
                          activePeriodKey.toLowerCase() === p
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:text-foreground",
                          !exists && "opacity-40 cursor-not-allowed",
                        )}
                      >
                        {PERIOD_LABELS[p] ?? p.toUpperCase()}
                      </button>
                    );
                  })}
                </div>

                {activePeriodStats ? (
                  <>
                    {/* Sample size info + small-sample warning */}
                    {activePeriodStats.sample_count != null && (
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{activePeriodStats.sample_count} decision{activePeriodStats.sample_count !== 1 ? "s" : ""} measured</span>
                        {activePeriodStats.sample_count < 30 && (
                          <span className="flex items-center gap-1 text-amber-400 font-semibold">
                            <AlertTriangle className="w-3 h-3" />
                            Low sample
                          </span>
                        )}
                      </div>
                    )}
                    {activePeriodStats.sample_count != null && activePeriodStats.sample_count < 30 && (
                      <div className="flex items-start gap-2 text-[11px] text-amber-400/90 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                        <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <span>
                          Only {activePeriodStats.sample_count} completed outcome{activePeriodStats.sample_count !== 1 ? "s" : ""}.
                          This is not statistically meaningful.
                        </span>
                      </div>
                    )}

                    {/* Stats grid */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-2 rounded-lg bg-muted/40">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Dir. Success</p>
                        <p className="text-base font-bold font-mono text-emerald-400">{fmtPct(activePeriodStats.directional_success)}</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted/40">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Profitable</p>
                        <p className="text-base font-bold font-mono text-primary">{fmtPct(activePeriodStats.profitable_after_costs)}</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted/40">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Avg Return</p>
                        <p className={cn("text-base font-bold font-mono", activePeriodStats.average_return != null && activePeriodStats.average_return >= 0 ? "text-emerald-400" : "text-destructive")}>
                          {activePeriodStats.average_return != null ? (activePeriodStats.average_return >= 0 ? "+" : "") + fmtPct(activePeriodStats.average_return) : "—"}
                        </p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted/40">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Net Return</p>
                        <p className={cn("text-base font-bold font-mono", activePeriodStats.average_net_return != null && activePeriodStats.average_net_return >= 0 ? "text-emerald-400" : "text-destructive")}>
                          {activePeriodStats.average_net_return != null ? (activePeriodStats.average_net_return >= 0 ? "+" : "") + fmtPct(activePeriodStats.average_net_return) : "—"}
                        </p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted/40">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Max Drawdown</p>
                        <p className="text-base font-bold font-mono text-destructive">{fmtPct(activePeriodStats.maximum_drawdown)}</p>
                      </div>
                      <div className="p-2 rounded-lg bg-muted/40">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Stability</p>
                        <p className="text-base font-bold font-mono text-sky-400">{fmtPct(activePeriodStats.rolling_stability)}</p>
                      </div>
                    </div>

                    {/* Coverage */}
                    {activePeriodStats.coverage != null && (
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] uppercase tracking-wider text-muted-foreground shrink-0">Coverage</span>
                        <Progress value={activePeriodStats.coverage * 100} className="flex-1 h-1.5" />
                        <span className="text-xs font-mono font-semibold text-muted-foreground shrink-0">
                          {fmtPct(activePeriodStats.coverage)}
                        </span>
                      </div>
                    )}

                    {/* Recharts bar chart */}
                    {shadowChartData.length > 0 && (
                      <div className="h-32">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={shadowChartData} margin={{ top: 0, right: 0, left: -24, bottom: 0 }}>
                            <XAxis
                              dataKey="name"
                              tick={{ fontSize: 9, fill: "#6b7280" }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              tick={{ fontSize: 9, fill: "#6b7280" }}
                              axisLine={false}
                              tickLine={false}
                              tickFormatter={(v) => `${v}%`}
                            />
                            <Tooltip
                              contentStyle={{ background: "#0a0a0a", border: "1px solid #1f2937", borderRadius: 8, fontSize: 11 }}
                              formatter={(v: number) => [`${v}%`, ""]}
                            />
                            <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={36}>
                              {shadowChartData.map((entry, i) => (
                                <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    No data for this period.
                  </p>
                )}

                {shadowPerf.generated_at && (
                  <p className="text-[10px] text-muted-foreground text-right">
                    Updated {timeAgo(shadowPerf.generated_at)}
                  </p>
                )}
              </div>
            ) : (
              <UnavailableState
                label={shadowPerf ? "Shadow performance data not yet available." : "No shadow performance data."}
                onRetry={() => refetchShadow()}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── 7. Top Opportunities ────────────────────────────────────────────── */}
      {snapshotLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-52" />)}
        </div>
      )}
      {!snapshotLoading && snapshot && snapshot.top_opportunities && snapshot.top_opportunities.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" />
            Top Opportunities
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {snapshot.top_opportunities.slice(0, 3).map((opp, i) => {
              const cls = (opp.classification ?? "").toUpperCase();
              const clsStyle =
                cls === "CANDIDATE" ? "text-emerald-400 border-emerald-500/25 bg-emerald-500/5" :
                cls === "WATCH" ? "text-primary border-primary/25 bg-primary/5" :
                cls === "MONITOR" ? "text-amber-400 border-amber-500/25 bg-amber-500/5" :
                cls === "BLOCKED" ? "text-destructive border-destructive/25 bg-destructive/5" :
                "text-muted-foreground border-border bg-muted/20";

              return (
                <button
                  key={i}
                  className="text-left rounded-xl border border-border bg-card p-4 flex flex-col gap-3 hover:border-primary/30 hover:bg-primary/5 transition-colors group"
                  onClick={() => setSelectedOpportunity(opp)}
                >
                  {/* Header row */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-muted-foreground font-mono">#{i + 1}</span>
                        <span className="text-lg font-black font-mono text-primary">{opp.ticker}</span>
                      </div>
                      <span className={cn(
                        "inline-block mt-0.5 text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded border",
                        clsStyle,
                      )}>
                        {cls || "—"}
                      </span>
                    </div>
                    {opp.score != null && (
                      <div className="text-right shrink-0">
                        <p className="text-[10px] text-muted-foreground">Score</p>
                        <p className="text-base font-black font-mono">{fmtNum(opp.score)}</p>
                      </div>
                    )}
                  </div>

                  {/* Headline */}
                  {!!(opp as Record<string, unknown>).headline && (
                    <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                      {String((opp as Record<string, unknown>).headline)}
                    </p>
                  )}

                  {/* Key metrics grid */}
                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
                    {opp.confidence != null && (
                      <div>
                        <span className="text-muted-foreground">Confidence </span>
                        <span className="font-semibold">{confPct(opp.confidence)}</span>
                      </div>
                    )}
                    {!!(opp as Record<string, unknown>).event_type && (
                      <div>
                        <span className="text-muted-foreground">Event </span>
                        <span className="font-semibold uppercase text-[9px]">
                          {String((opp as Record<string, unknown>).event_type)}
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-muted-foreground">Material </span>
                      <span className={cn("font-semibold", opp.material_event ? "text-amber-400" : "text-muted-foreground")}>
                        {opp.material_event ? "YES" : "NO"}
                      </span>
                    </div>
                    {(opp as Record<string, unknown>).eligible_for_trade != null && (
                      <div>
                        <span className="text-muted-foreground">Eligible </span>
                        <span className={cn("font-semibold", (opp as Record<string, unknown>).eligible_for_trade ? "text-emerald-400" : "text-muted-foreground")}>
                          {(opp as Record<string, unknown>).eligible_for_trade ? "YES" : "NO"}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Blocking reasons */}
                  {opp.blocking_reasons && opp.blocking_reasons.length > 0 && (
                    <div className="flex items-start gap-1.5 text-[11px] text-destructive">
                      <XCircle className="w-3 h-3 shrink-0 mt-0.5" />
                      <span className="line-clamp-2">{renderReason(opp.blocking_reasons[0])}</span>
                    </div>
                  )}

                  {/* Reasons (when no blockers) */}
                  {(!opp.blocking_reasons || opp.blocking_reasons.length === 0) &&
                    opp.reasons && opp.reasons.length > 0 && (
                      <div className="space-y-0.5">
                        {opp.reasons.slice(0, 2).map((r, ri) => (
                          <div key={ri} className="flex items-start gap-1.5 text-[11px] text-muted-foreground">
                            <CheckCircle2 className="w-3 h-3 shrink-0 mt-0.5 text-emerald-500/60" />
                            <span className="line-clamp-1">{renderReason(r)}</span>
                          </div>
                        ))}
                      </div>
                    )}

                  <p className="text-[10px] text-primary/50 font-semibold group-hover:text-primary transition-colors mt-auto">
                    View details →
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Opportunity Detail Drawer ─────────────────────────────────────────── */}
      <Sheet open={!!selectedOpportunity} onOpenChange={(open) => { if (!open) setSelectedOpportunity(null); }}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedOpportunity && (() => {
            const cls = (selectedOpportunity.classification ?? "").toUpperCase();
            const clsStyle =
              cls === "CANDIDATE" ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" :
              cls === "WATCH" ? "text-primary border-primary/30 bg-primary/10" :
              cls === "MONITOR" ? "text-amber-400 border-amber-500/30 bg-amber-500/10" :
              cls === "BLOCKED" ? "text-destructive border-destructive/30 bg-destructive/10" :
              "text-muted-foreground border-border bg-muted/20";
            const opp = selectedOpportunity as TopOpportunity & Record<string, unknown>;
            return (
              <>
                <SheetHeader className="mb-6">
                  <div className="flex items-center gap-3 flex-wrap">
                    <SheetTitle className="text-2xl font-black font-mono text-primary">
                      {selectedOpportunity.ticker}
                    </SheetTitle>
                    <span className={cn("text-[11px] font-bold uppercase tracking-widest px-2 py-0.5 rounded border", clsStyle)}>
                      {cls || "—"}
                    </span>
                  </div>
                  {!!opp.headline && (
                    <p className="text-sm text-muted-foreground leading-relaxed mt-1">
                      {String(opp.headline)}
                    </p>
                  )}
                </SheetHeader>

                <div className="space-y-6">
                  {/* Score breakdown */}
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                      Score Breakdown
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      {selectedOpportunity.score != null && (
                        <div className="p-3 rounded-lg bg-muted/40">
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Score</p>
                          <p className="text-xl font-black font-mono">{fmtNum(selectedOpportunity.score)}</p>
                        </div>
                      )}
                      {selectedOpportunity.confidence != null && (
                        <div className="p-3 rounded-lg bg-muted/40">
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Confidence</p>
                          <p className="text-xl font-black font-mono">{confPct(selectedOpportunity.confidence)}</p>
                        </div>
                      )}
                      {!!opp.evidence_maturity && (
                        <div className="p-3 rounded-lg bg-muted/40">
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Evidence Maturity</p>
                          <p className="text-sm font-bold">{String(opp.evidence_maturity)}</p>
                        </div>
                      )}
                      {opp.eligible_for_trade != null && (
                        <div className="p-3 rounded-lg bg-muted/40">
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Trade Eligible</p>
                          <p className={cn("text-sm font-bold", opp.eligible_for_trade ? "text-emerald-400" : "text-muted-foreground")}>
                            {opp.eligible_for_trade ? "YES" : "NO"}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Signal details */}
                  <div className="space-y-2">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Signal Details
                    </p>
                    {!!opp.event_type && (
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-muted-foreground">Event Type</span>
                        <span className="font-semibold uppercase text-xs">{String(opp.event_type)}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Material Event</span>
                      <span className={cn("font-semibold", selectedOpportunity.material_event ? "text-amber-400" : "text-muted-foreground")}>
                        {selectedOpportunity.material_event ? "YES" : "NO"}
                      </span>
                    </div>
                    {selectedOpportunity.current_status && (
                      <div className="flex justify-between items-start text-sm gap-4">
                        <span className="text-muted-foreground shrink-0">Status</span>
                        <span className="text-xs text-right">{selectedOpportunity.current_status}</span>
                      </div>
                    )}
                    {!!opp.shadow_analysis_status && (
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-muted-foreground">Shadow Analysis</span>
                        <span className="font-semibold">{String(opp.shadow_analysis_status)}</span>
                      </div>
                    )}
                  </div>

                  {/* Reasons */}
                  {Array.isArray(selectedOpportunity.reasons) && selectedOpportunity.reasons.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                        Reasons
                      </p>
                      <ul className="space-y-1.5">
                        {selectedOpportunity.reasons.map((r, ri) => (
                          <li key={ri} className="flex items-start gap-2 text-sm">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                            <span>{renderReason(r)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Blockers */}
                  {Array.isArray(selectedOpportunity.blocking_reasons) && selectedOpportunity.blocking_reasons.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                        Blockers
                      </p>
                      <ul className="space-y-1.5">
                        {selectedOpportunity.blocking_reasons.map((r, ri) => (
                          <li key={ri} className="flex items-start gap-2 text-sm text-destructive">
                            <XCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                            <span>{renderReason(r)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Related article */}
                  {!!opp.article_id && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                        Related Article
                      </p>
                      <p className="text-xs font-mono text-muted-foreground break-all">{String(opp.article_id)}</p>
                      {!!opp.source && (
                        <p className="text-xs text-muted-foreground mt-1">Source: {String(opp.source)}</p>
                      )}
                    </div>
                  )}
                </div>
              </>
            );
          })()}
        </SheetContent>
      </Sheet>

      {/* ── 8. Recent Activity ───────────────────────────────────────────────── */}
      <div>
        <h2 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5" />
          Recent Activity
        </h2>
        <Card>
          <div className="divide-y divide-border">
            {runHistoryResp ? (
              runHistory.length > 0 ? (
                runHistory.slice(0, 10).map((run) => (
                  <div
                    key={run.run_id}
                    className="px-4 py-3 flex items-center justify-between hover:bg-muted/40 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <StatusBadge status={run.status || "UNKNOWN"} className="w-24 justify-center shrink-0" />
                      <div>
                        <p className="text-sm font-medium">{labelForRunType(run.run_type)}</p>
                        <p className="text-xs text-muted-foreground font-mono">
                          {formatDate(run.started_at)}
                          {run.provider && <span className="ml-2 opacity-60">· {run.provider}</span>}
                        </p>
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                      {run.duration_seconds != null && (
                        <p className="text-xs font-mono text-muted-foreground">{run.duration_seconds.toFixed(1)}s</p>
                      )}
                      {run.failure_count > 0 && (
                        <p className="text-[11px] text-destructive">{run.failure_count} failed</p>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-muted-foreground text-sm">No recent activity</div>
              )
            ) : (
              <div className="p-4 space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
