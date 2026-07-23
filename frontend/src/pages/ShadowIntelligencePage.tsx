import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  ShadowPerformanceReport,
  GraduationStatus,
  ListResponse,
} from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate, cn } from "@/lib/utils";
import {
  Brain,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  GraduationCap,
  BarChart2,
  Clock,
  Activity,
  Filter,
} from "lucide-react";

// ─── Shadow decision type (from /api/shadow-decisions) ───────────────────────

interface ShadowDecision {
  decision_id: string;
  symbol: string;
  action: string;
  score: number | null;
  confidence: number | null;
  event_type: string | null;
  is_material: boolean;
  headline: string | null;
  eligible_for_trade: boolean;
  reasons: unknown[];
  blocking_reasons: unknown[];
  reference_price: number | null;
  reference_captured_at: string | null;
  model_version: string | null;
  created_at: string;
}

interface ShadowDecisionSummary {
  total_decisions: number;
  measured_decisions: number;
  eligible_decisions: number;
  blocked_decisions: number;
  latest_decision_at: string | null;
  model_version: string | null;
  [key: string]: unknown;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return (v <= 1 ? v * 100 : v).toFixed(1) + "%";
}

function fmtNum(v: number | null | undefined, decimals = 2): string {
  if (v == null) return "—";
  return v.toFixed(decimals);
}

function renderReason(item: unknown): string {
  if (!item) return "";
  if (typeof item === "string") return item;
  if (typeof item === "object") {
    const o = item as Record<string, unknown>;
    return (
      (typeof o.reason === "string" ? o.reason : null) ??
      (typeof o.message === "string" ? o.message : null) ??
      (typeof o.text === "string" ? o.text : null) ??
      JSON.stringify(item)
    );
  }
  return String(item);
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

// ─── Summary Section ──────────────────────────────────────────────────────────

function SummarySection() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["shadow-decisions-summary"],
    queryFn: () => apiClient.get<ShadowDecisionSummary>("/shadow-decisions/summary"),
    refetchInterval: 60_000,
    retry: 1,
  });

  const cards = data
    ? [
        { label: "Total Decisions", value: data.total_decisions ?? "—" },
        { label: "Measured", value: data.measured_decisions ?? "—" },
        { label: "Eligible for Trade", value: data.eligible_decisions ?? "—", color: "text-emerald-400" },
        { label: "Blocked", value: data.blocked_decisions ?? "—", color: "text-destructive" },
      ]
    : [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Activity className="w-3.5 h-3.5" />
          Decision Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : isError ? (
          <UnavailableState label="Decision summary unavailable." onRetry={() => refetch()} />
        ) : data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {cards.map((c) => (
                <div key={c.label} className="flex flex-col gap-1 p-3 rounded-lg bg-muted/40">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                    {c.label}
                  </span>
                  <span className={cn("text-2xl font-black font-mono", c.color ?? "text-foreground")}>
                    {c.value}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground border-t border-border pt-3">
              {data.latest_decision_at && (
                <span>Latest: {formatDate(data.latest_decision_at)}</span>
              )}
              {data.model_version && (
                <span className="font-mono">Model: {data.model_version}</span>
              )}
            </div>
          </div>
        ) : (
          <UnavailableState label="No decision data yet." onRetry={() => refetch()} />
        )}
      </CardContent>
    </Card>
  );
}

// ─── Performance Section ──────────────────────────────────────────────────────

const PERIOD_ORDER = ["1h", "1d", "5d"];

const METRICS: { key: string; label: string }[] = [
  { key: "coverage", label: "Coverage" },
  { key: "directional_success", label: "Directional Success" },
  { key: "profitable_after_costs", label: "Profitable After Cost" },
  { key: "average_return", label: "Avg Return" },
  { key: "average_net_return", label: "Avg Net Return" },
  { key: "maximum_drawdown", label: "Max Drawdown" },
  { key: "rolling_stability", label: "Rolling Stability" },
  { key: "sample_count", label: "Sample Count" },
];

function PerformanceSection() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["shadow-performance"],
    queryFn: () => apiClient.get<ShadowPerformanceReport>("/shadow-performance"),
    refetchInterval: 60_000,
    retry: 1,
  });

  const periods = data?.periods ? Object.keys(data.periods) : [];
  const orderedPeriods = [
    ...PERIOD_ORDER.filter((p) => periods.includes(p)),
    ...periods.filter((p) => !PERIOD_ORDER.includes(p)),
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <BarChart2 className="w-3.5 h-3.5" />
          Performance Metrics
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : isError ? (
          <UnavailableState label="Performance data unavailable." onRetry={() => refetch()} />
        ) : data && data.available && orderedPeriods.length > 0 ? (
          <div className="space-y-3">
            {data.generated_at && (
              <p className="text-[11px] text-muted-foreground">
                Generated {formatDate(data.generated_at)}
              </p>
            )}
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="w-48">Metric</TableHead>
                    {orderedPeriods.map((p) => (
                      <TableHead key={p} className="text-center">
                        {p.toUpperCase()}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {METRICS.map(({ key, label }) => (
                    <TableRow key={key}>
                      <TableCell className="text-xs text-muted-foreground font-medium">
                        {label}
                      </TableCell>
                      {orderedPeriods.map((p) => {
                        const stats = data.periods[p];
                        const val = stats?.[key];
                        const isCount = key === "sample_count";
                        const formatted = isCount
                          ? (val == null ? "—" : String(val))
                          : fmtPct(val as number | null);
                        const lowSample =
                          isCount && typeof val === "number" && val < 10;
                        return (
                          <TableCell
                            key={p}
                            className={cn(
                              "text-center text-xs font-mono",
                              lowSample && "text-amber-400",
                            )}
                          >
                            {formatted}
                            {lowSample && (
                              <span className="ml-1 text-[10px] text-amber-400" title="Low sample count">
                                ⚠
                              </span>
                            )}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ) : (
          <UnavailableState
            label={
              data && !data.available
                ? "Performance report not yet available — run shadow analysis first."
                : "No performance data available."
            }
            onRetry={() => refetch()}
          />
        )}
      </CardContent>
    </Card>
  );
}

// ─── Graduation Section ───────────────────────────────────────────────────────

function GraduationSection() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["intelligence-graduation"],
    queryFn: () => apiClient.get<GraduationStatus>("/intelligence/graduation-status"),
    refetchInterval: 60_000,
    retry: 1,
  });

  const gradTotal = data
    ? (data.checks_passed ?? 0) + (data.checks_remaining ?? 0)
    : 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <GraduationCap className="w-3.5 h-3.5" />
          Graduation Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-2 w-full" />
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-5 w-full" />)}
          </div>
        ) : isError ? (
          <UnavailableState label="Graduation status unavailable." onRetry={() => refetch()} />
        ) : data ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
                  Stage
                </p>
                <p className="text-sm font-bold">
                  {(data.stage ?? "").replace(/_/g, " ")}
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-black font-mono text-primary">
                  {gradTotal > 0
                    ? Math.round(((data.checks_passed ?? 0) / gradTotal) * 100)
                    : 0}
                  %
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {data.checks_passed ?? 0}/{gradTotal} checks
                </p>
              </div>
            </div>

            {/* Checks list */}
            {Array.isArray(data.checks) && data.checks.length > 0 && (
              <div className="space-y-2 border-t border-border pt-3">
                {data.checks.map((check, i) => (
                  <div key={i} className="flex items-start gap-2">
                    {check.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className={cn("text-xs font-medium", check.passed ? "text-foreground" : "text-muted-foreground")}>
                        {check.name}
                      </p>
                      {check.description && (
                        <p className="text-[11px] text-muted-foreground italic">
                          {check.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-2 px-3 py-2 rounded-md bg-muted/40 border border-border text-xs text-muted-foreground">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-400" />
              Passing graduation does not enable trading automatically. Manual
              confirmation is always required.
            </div>
          </div>
        ) : (
          <UnavailableState label="No graduation data." onRetry={() => refetch()} />
        )}
      </CardContent>
    </Card>
  );
}

// ─── Decision History ─────────────────────────────────────────────────────────

type ActionFilter = "ALL" | "BUY" | "SELL" | "HOLD";
type EligibilityFilter = "ALL" | "ELIGIBLE" | "BLOCKED";
type MaterialityFilter = "ALL" | "MATERIAL" | "NON_MATERIAL";

function DecisionHistorySection() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["shadow-decisions"],
    queryFn: () => apiClient.get<ListResponse<ShadowDecision>>("/shadow-decisions"),
    refetchInterval: 60_000,
    retry: 1,
  });

  const [symbolFilter, setSymbolFilter] = useState("");
  const [actionFilter, setActionFilter] = useState<ActionFilter>("ALL");
  const [eligibilityFilter, setEligibilityFilter] = useState<EligibilityFilter>("ALL");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [materialityFilter, setMaterialityFilter] = useState<MaterialityFilter>("ALL");
  const [modelFilter, setModelFilter] = useState("");

  const decisions = data?.items ?? [];

  const filtered = useMemo(() => {
    return decisions.filter((d) => {
      if (symbolFilter && !d.symbol.toLowerCase().includes(symbolFilter.toLowerCase()))
        return false;
      if (actionFilter !== "ALL" && d.action?.toUpperCase() !== actionFilter)
        return false;
      if (eligibilityFilter === "ELIGIBLE" && !d.eligible_for_trade) return false;
      if (eligibilityFilter === "BLOCKED" && d.eligible_for_trade) return false;
      if (
        eventTypeFilter &&
        !d.event_type?.toLowerCase().includes(eventTypeFilter.toLowerCase())
      )
        return false;
      if (materialityFilter === "MATERIAL" && !d.is_material) return false;
      if (materialityFilter === "NON_MATERIAL" && d.is_material) return false;
      if (
        modelFilter &&
        !d.model_version?.toLowerCase().includes(modelFilter.toLowerCase())
      )
        return false;
      return true;
    });
  }, [decisions, symbolFilter, actionFilter, eligibilityFilter, eventTypeFilter, materialityFilter, modelFilter]);

  const hasFilters =
    symbolFilter ||
    actionFilter !== "ALL" ||
    eligibilityFilter !== "ALL" ||
    eventTypeFilter ||
    materialityFilter !== "ALL" ||
    modelFilter;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Clock className="w-3.5 h-3.5" />
          Decision History
          {data && (
            <span className="ml-auto text-[10px] text-muted-foreground font-normal">
              {filtered.length} / {decisions.length}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filter bar */}
        <div className="flex flex-wrap gap-2">
          <Input
            placeholder="Symbol"
            value={symbolFilter}
            onChange={(e) => setSymbolFilter(e.target.value)}
            className="h-8 w-28 text-xs"
            data-testid="filter-symbol"
          />
          <Select
            value={actionFilter}
            onValueChange={(v) => setActionFilter(v as ActionFilter)}
          >
            <SelectTrigger className="h-8 w-28 text-xs" data-testid="filter-action">
              <SelectValue placeholder="Action" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Actions</SelectItem>
              <SelectItem value="BUY">Buy</SelectItem>
              <SelectItem value="SELL">Sell</SelectItem>
              <SelectItem value="HOLD">Hold</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={eligibilityFilter}
            onValueChange={(v) => setEligibilityFilter(v as EligibilityFilter)}
          >
            <SelectTrigger className="h-8 w-32 text-xs" data-testid="filter-eligibility">
              <SelectValue placeholder="Eligibility" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All</SelectItem>
              <SelectItem value="ELIGIBLE">Eligible</SelectItem>
              <SelectItem value="BLOCKED">Blocked</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={materialityFilter}
            onValueChange={(v) => setMaterialityFilter(v as MaterialityFilter)}
          >
            <SelectTrigger className="h-8 w-36 text-xs" data-testid="filter-materiality">
              <SelectValue placeholder="Materiality" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All</SelectItem>
              <SelectItem value="MATERIAL">Material</SelectItem>
              <SelectItem value="NON_MATERIAL">Non-Material</SelectItem>
            </SelectContent>
          </Select>
          <Input
            placeholder="Event type"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="h-8 w-32 text-xs"
            data-testid="filter-event-type"
          />
          <Input
            placeholder="Model version"
            value={modelFilter}
            onChange={(e) => setModelFilter(e.target.value)}
            className="h-8 w-32 text-xs"
            data-testid="filter-model-version"
          />
          {hasFilters && (
            <Button
              size="sm"
              variant="ghost"
              className="h-8 text-xs text-muted-foreground"
              onClick={() => {
                setSymbolFilter("");
                setActionFilter("ALL");
                setEligibilityFilter("ALL");
                setEventTypeFilter("");
                setMaterialityFilter("ALL");
                setModelFilter("");
              }}
            >
              Clear
            </Button>
          )}
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : isError ? (
          <UnavailableState label="Decision history unavailable." onRetry={() => refetch()} />
        ) : filtered.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            {hasFilters ? "No decisions match the current filters." : "No shadow decisions recorded yet."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Time</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Material</TableHead>
                  <TableHead>Eligible</TableHead>
                  <TableHead className="max-w-xs">Headline</TableHead>
                  <TableHead>Reasons</TableHead>
                  <TableHead>Blocking</TableHead>
                  <TableHead>Ref Price</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.slice(0, 200).map((d) => (
                  <TableRow key={d.decision_id} className="align-top">
                    <TableCell className="text-[11px] font-mono whitespace-nowrap">
                      {formatDate(d.created_at)}
                    </TableCell>
                    <TableCell className="text-sm font-bold font-mono text-primary">
                      {d.symbol}
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "text-[11px] font-bold uppercase",
                          d.action?.toUpperCase() === "BUY"
                            ? "text-emerald-400"
                            : d.action?.toUpperCase() === "SELL"
                              ? "text-destructive"
                              : "text-muted-foreground",
                        )}
                      >
                        {d.action ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {fmtNum(d.score)}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {fmtPct(d.confidence)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {d.event_type ?? "—"}
                    </TableCell>
                    <TableCell>
                      {d.is_material ? (
                        <span className="text-[11px] font-bold text-amber-400">YES</span>
                      ) : (
                        <span className="text-[11px] text-muted-foreground">No</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {d.eligible_for_trade ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-muted-foreground" />
                      )}
                    </TableCell>
                    <TableCell className="text-[11px] max-w-[200px] truncate" title={d.headline ?? undefined}>
                      {d.headline ?? "—"}
                    </TableCell>
                    <TableCell className="text-[11px] text-muted-foreground max-w-[160px]">
                      {Array.isArray(d.reasons) && d.reasons.length > 0
                        ? d.reasons.slice(0, 2).map(renderReason).join("; ")
                        : "—"}
                    </TableCell>
                    <TableCell className="text-[11px] text-destructive max-w-[160px]">
                      {Array.isArray(d.blocking_reasons) && d.blocking_reasons.length > 0
                        ? d.blocking_reasons.slice(0, 2).map(renderReason).join("; ")
                        : "—"}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {d.reference_price != null ? `$${d.reference_price.toFixed(2)}` : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filtered.length > 200 && (
              <p className="text-[11px] text-muted-foreground text-center py-2">
                Showing 200 of {filtered.length} decisions. Use filters to narrow results.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ShadowIntelligencePage() {
  return (
    <div className="space-y-5 max-w-7xl">
      <div className="flex items-center gap-2">
        <Brain className="w-4 h-4 text-primary" />
        <h2 className="text-sm font-semibold uppercase tracking-wider">
          Shadow Intelligence
        </h2>
      </div>

      <p className="text-xs text-muted-foreground -mt-2">
        Read-only view of AI shadow trading decisions and performance. No trades
        are executed — this is research observation only.
      </p>

      <SummarySection />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <PerformanceSection />
        <GraduationSection />
      </div>

      <DecisionHistorySection />
    </div>
  );
}
