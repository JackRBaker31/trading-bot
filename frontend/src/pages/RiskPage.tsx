import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { RiskStatus, ReconciliationStatus, AppStatus } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { formatGBP, cn } from "@/lib/utils";
import {
  ShieldCheck,
  AlertOctagon,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
} from "lucide-react";

// ─── Readiness check helpers ──────────────────────────────────────────────────

interface ReadinessItem {
  label: string;
  passed: boolean;
  severity: "critical" | "warning" | "info";
  /** Shown when the check fails — must be actionable. */
  blocker?: string;
}

function buildReadinessChecks(
  risk: RiskStatus,
  recon: ReconciliationStatus,
): ReadinessItem[] {
  return [
    {
      label: "Paper trading enabled",
      passed: risk.paper_trading_enabled,
      severity: "critical",
      blocker:
        "Paper trading is disabled in the current configuration. Enable it via the backend configuration before starting.",
    },
    {
      label: "Execution permission confirmed",
      passed: risk.execution_permission_confirmed,
      severity: "warning",
      blocker:
        "Execution permission has not been confirmed. The system will not submit orders until this is acknowledged in the backend.",
    },
    {
      label: "Real-money trading disabled",
      passed: !risk.real_money_trading_enabled,
      severity: "critical",
      blocker:
        "⚠ Real-money trading is ENABLED — this is unexpected in a demo environment. Disable it immediately before running.",
    },
    {
      label: "No unresolved orders",
      passed: recon.unresolved_order_count === 0,
      severity: "warning",
      blocker: `${recon.unresolved_order_count} unresolved order(s) found. Go to the Orders page and resolve them before starting.`,
    },
    {
      label: "Reconciliation safe-to-start",
      passed: recon.safe_to_start,
      severity: "critical",
      blocker:
        "Reconciliation check failed. The system considers it unsafe to start. Resolve any unresolved orders and retry reconciliation.",
    },
    {
      label: "Reconciliation data available",
      passed: recon.available,
      severity: "info",
      blocker:
        "No reconciliation data is available yet. Run a reconciliation cycle first.",
    },
  ];
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex justify-between items-center py-2.5 border-b border-border/50 last:border-0 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <div className="font-mono text-right">{children}</div>
    </div>
  );
}

function EnvBadge({ value }: { value: string }) {
  return (
    <span className="px-2 py-0.5 rounded text-[10px] font-bold border border-[#D4AF37]/30 text-[#D4AF37] bg-[#D4AF37]/10 uppercase">
      {value}
    </span>
  );
}

function CheckRow({ item }: { item: ReadinessItem }) {
  const icon = item.passed ? (
    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
  ) : item.severity === "critical" ? (
    <XCircle className="w-4 h-4 text-destructive shrink-0" />
  ) : item.severity === "warning" ? (
    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
  ) : (
    <Info className="w-4 h-4 text-muted-foreground shrink-0" />
  );

  return (
    <div
      className={cn(
        "rounded-lg border p-3 space-y-1.5",
        item.passed
          ? "bg-emerald-500/5 border-emerald-500/10"
          : item.severity === "critical"
            ? "bg-destructive/10 border-destructive/20"
            : item.severity === "warning"
              ? "bg-amber-500/10 border-amber-500/20"
              : "bg-muted/30 border-border",
      )}
    >
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm font-medium">{item.label}</span>
        <span
          className={cn(
            "ml-auto text-[10px] font-bold uppercase px-1.5 py-0.5 rounded",
            item.passed
              ? "text-emerald-400"
              : item.severity === "critical"
                ? "text-destructive"
                : item.severity === "warning"
                  ? "text-amber-400"
                  : "text-muted-foreground",
          )}
        >
          {item.passed ? "PASS" : "FAIL"}
        </span>
      </div>
      {!item.passed && item.blocker && (
        <p
          className={cn(
            "text-xs pl-6 leading-relaxed",
            item.severity === "critical"
              ? "text-destructive/80"
              : item.severity === "warning"
                ? "text-amber-400/80"
                : "text-muted-foreground",
          )}
        >
          {item.blocker}
        </p>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function RiskPage() {
  const { data: risk, isLoading: riskLoading } = useQuery({
    queryKey: ["risk-status"],
    queryFn: () => apiClient.get<RiskStatus>("/risk/status"),
    refetchInterval: 30_000,
  });

  const { data: recon, isLoading: reconLoading } = useQuery({
    queryKey: ["reconciliation-latest"],
    queryFn: () => apiClient.get<ReconciliationStatus>("/reconciliation/latest"),
    refetchInterval: 30_000,
  });

  const { data: appStatus } = useQuery({
    queryKey: ["api-status"],
    queryFn: () => apiClient.get<AppStatus>("/status"),
    staleTime: 60_000,
  });

  const isLoading = riskLoading || reconLoading;
  const readinessItems =
    risk && recon ? buildReadinessChecks(risk, recon) : [];
  const criticalFails = readinessItems.filter(
    (i) => !i.passed && i.severity === "critical",
  );
  const allPassed = readinessItems.length > 0 && readinessItems.every((i) => i.passed);

  return (
    <div className="space-y-6 max-w-4xl">
      <h2 className="text-sm font-semibold uppercase tracking-wider">
        Risk &amp; Reconciliation
      </h2>

      {/* ── Overall readiness banner ──────────────────────────────────────── */}
      {!isLoading && risk && recon && (
        <div
          className={cn(
            "p-4 rounded-lg border flex items-start gap-4",
            allPassed
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : criticalFails.length > 0
                ? "bg-destructive/10 border-destructive/30 text-destructive"
                : "bg-amber-500/10 border-amber-500/20 text-amber-400",
          )}
        >
          {allPassed ? (
            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
          ) : (
            <AlertOctagon className="w-5 h-5 shrink-0 mt-0.5" />
          )}
          <div>
            <p className="font-bold text-sm uppercase tracking-wide">
              {allPassed
                ? "All readiness checks passed — safe to start"
                : criticalFails.length > 0
                  ? `${criticalFails.length} critical blocker${criticalFails.length > 1 ? "s" : ""} — not safe to start`
                  : "Non-critical warnings — review before starting"}
            </p>
            {!allPassed && (
              <p className="text-xs mt-1 opacity-80">
                Review the readiness checks below and resolve each blocker.
              </p>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Limits ─────────────────────────────────────────────────────────── */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-primary" />
              Risk Limits
            </CardTitle>
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : risk ? (
              <>
                <StatusRow label="Max Order Value">
                  {formatGBP(risk.max_order_value)}
                </StatusRow>
                <StatusRow label="Max Position Value">
                  {formatGBP(risk.max_position_value)}
                </StatusRow>
                <StatusRow label="Max Portfolio Exposure">
                  <span>
                    {(risk.max_portfolio_exposure_ratio * 100).toFixed(0)}%
                    {risk.max_portfolio_exposure_value > 0 && (
                      <span className="text-muted-foreground ml-1 text-xs">
                        ({formatGBP(risk.max_portfolio_exposure_value)})
                      </span>
                    )}
                  </span>
                </StatusRow>
                <StatusRow label="Max Trades / Session">
                  {risk.max_trades_per_session}
                </StatusRow>
                <div className="pt-3">
                  <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider">
                    Approved Symbols
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {risk.approved_symbols.length > 0 ? (
                      risk.approved_symbols.map((sym) => (
                        <Badge
                          key={sym}
                          variant="outline"
                          className="font-mono text-[10px] uppercase bg-card"
                        >
                          {sym}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground italic">
                        No approved symbols configured
                      </span>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Failed to load risk data.</p>
            )}
          </CardContent>
        </Card>

        {/* ── Environment ─────────────────────────────────────────────────────── */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Environment
            </CardTitle>
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : risk ? (
              <>
                <StatusRow label="Broker Environment">
                  <EnvBadge value={risk.broker_environment} />
                </StatusRow>
                <StatusRow label="Application Mode">
                  {appStatus ? (
                    <EnvBadge value={appStatus.application_mode} />
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </StatusRow>
                <StatusRow label="Market Data Provider">
                  {appStatus ? (
                    <span className="text-xs font-mono">{appStatus.market_data_provider}</span>
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </StatusRow>
                <StatusRow label="Execution Permission">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                      risk.execution_permission_confirmed
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-amber-500/10 text-amber-400",
                    )}
                  >
                    {risk.execution_permission_confirmed ? "Confirmed" : "Not Confirmed"}
                  </span>
                </StatusRow>
                <StatusRow label="Real-Money Trading">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                      risk.real_money_trading_enabled
                        ? "bg-destructive/10 text-destructive"
                        : "bg-emerald-500/10 text-emerald-400",
                    )}
                  >
                    {risk.real_money_trading_enabled ? "ENABLED ⚠" : "DISABLED ✓"}
                  </span>
                </StatusRow>
                <StatusRow label="Paper Trading">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                      risk.paper_trading_enabled
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-muted text-muted-foreground",
                    )}
                  >
                    {risk.paper_trading_enabled ? "Enabled" : "Disabled"}
                  </span>
                </StatusRow>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Failed to load environment data.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Readiness Checks ─────────────────────────────────────────────────── */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Readiness Checks
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : readinessItems.length > 0 ? (
            <div className="space-y-2">
              {readinessItems.map((item) => (
                <CheckRow key={item.label} item={item} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground py-4 text-center">
              Unable to evaluate readiness — risk and reconciliation data unavailable.
            </p>
          )}
        </CardContent>
      </Card>

      {/* ── Reconciliation Detail ────────────────────────────────────────────── */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Reconciliation Detail
          </CardTitle>
        </CardHeader>
        <CardContent>
          {reconLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : recon ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Available",        value: recon.available ? "Yes" : "No" },
                { label: "Unresolved Orders", value: String(recon.unresolved_order_count) },
                { label: "Safe to Start",    value: recon.safe_to_start ? "Yes" : "No" },
                {
                  label: "Latest Run",
                  value: recon.latest_run
                    ? Object.keys(recon.latest_run).length > 0
                      ? "Available"
                      : "Empty"
                    : "None",
                },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-lg bg-muted/30 border border-border/50">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                    {label}
                  </p>
                  <p
                    className="text-sm font-mono font-medium"
                    data-testid={
                      label === "Safe to Start" ? "indicator-safe-to-start" : undefined
                    }
                  >
                    {value}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No reconciliation data available. Run a reconciliation cycle via the backend.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
