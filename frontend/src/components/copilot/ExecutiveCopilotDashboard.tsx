import React from "react";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CalendarClock,
  CheckCircle2,
  CircleGauge,
  Info,
  LockKeyhole,
  PlayCircle,
  RefreshCw,
  Server,
  ShieldCheck,
  Target,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  CopilotAttentionItem,
  CopilotOverview,
} from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";


type MetricStatus =
  | "healthy"
  | "warning"
  | "danger"
  | "info";


function displayName(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


function formatTimestamp(
  value: string,
): string {
  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-GB",
    {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "short",
    },
  ).format(date);
}


function relativeTimestamp(
  value: string,
): string {
  const timestamp =
    new Date(value).getTime();

  if (
    Number.isNaN(timestamp)
  ) {
    return "";
  }

  const seconds = Math.max(
    0,
    Math.round(
      (
        timestamp -
        Date.now()
      ) / 1000,
    ),
  );

  if (seconds < 60) {
    return `in ${seconds}s`;
  }

  const minutes =
    Math.floor(seconds / 60);

  if (minutes < 60) {
    return `in ${minutes}m`;
  }

  const hours =
    Math.floor(minutes / 60);

  const remainingMinutes =
    minutes % 60;

  if (remainingMinutes === 0) {
    return `in ${hours}h`;
  }

  return (
    `in ${hours}h ` +
    `${remainingMinutes}m`
  );
}


function confidencePercentage(
  confidence: number,
): number {
  if (!Number.isFinite(confidence)) {
    return 0;
  }

  const value =
    confidence <= 1
      ? confidence * 100
      : confidence;

  return Math.max(
    0,
    Math.min(
      100,
      value,
    ),
  );
}


function confidenceDisplay(
  confidence: number,
): string {
  return (
    `${confidencePercentage(
      confidence,
    ).toFixed(1)}%`
  );
}


function confidenceStatus(
  confidence: number,
): MetricStatus {
  const percentage =
    confidencePercentage(
      confidence,
    );

  if (percentage >= 80) {
    return "healthy";
  }

  if (percentage >= 50) {
    return "warning";
  }

  return "danger";
}


function OverviewMetricCard({
  title,
  value,
  detail,
  icon: Icon,
  status = "info",
}: {
  title: string;
  value: string;
  detail: string;
  icon: typeof Server;
  status?: MetricStatus;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-5",
        status === "healthy" &&
          "border-emerald-500/25",
        status === "warning" &&
          "border-amber-500/25",
        status === "danger" &&
          "border-destructive/30",
        status === "info" &&
          "border-border",
      )}
      data-testid="copilot-overview-card"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            {title}
          </p>

          <p className="mt-2 truncate text-2xl font-semibold">
            {value}
          </p>
        </div>

        <div
          className={cn(
            "ml-3 rounded-lg border p-2.5",
            status === "healthy" &&
              "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
            status === "warning" &&
              "border-amber-500/20 bg-amber-500/10 text-amber-400",
            status === "danger" &&
              "border-destructive/20 bg-destructive/10 text-destructive",
            status === "info" &&
              "border-primary/20 bg-primary/10 text-primary",
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
        {detail}
      </p>
    </div>
  );
}


function AttentionItemCard({
  item,
}: {
  item: CopilotAttentionItem;
}) {
  const isWarning =
    item.severity.toUpperCase() ===
    "WARNING";

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        isWarning
          ? "border-amber-500/25 bg-amber-500/5"
          : "border-primary/20 bg-primary/5",
      )}
    >
      <div className="flex items-start gap-3">
        {isWarning ? (
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
        ) : (
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        )}

        <div>
          <p className="text-sm font-medium">
            {item.title}
          </p>

          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            {item.detail}
          </p>
        </div>
      </div>
    </div>
  );
}


function TradingDecisionPanel({
  overview,
}: {
  overview: CopilotOverview;
}) {
  const intelligence =
    overview.trading_intelligence;

  const graduation =
    overview.graduation;

  const failedChecks =
    graduation.checks.filter(
      (check) => !check.passed,
    );

  const blockers = [
    ...(intelligence.trading_readiness !==
    "READY"
      ? [
          "Trading readiness has not reached READY.",
        ]
      : []),
    ...(confidencePercentage(
      intelligence.confidence,
    ) < 80
      ? [
          `Confidence is ${confidenceDisplay(
            intelligence.confidence,
          )}; the executive threshold is 80.0%.`,
        ]
      : []),
    ...(intelligence.actionable_signal_count <=
    0
      ? [
          "No actionable signals are currently available.",
        ]
      : []),
    ...(
      [
        "LOW",
        "INSUFFICIENT",
        "UNKNOWN",
      ].includes(
        intelligence.evidence_quality
          .toUpperCase(),
      )
        ? [
            `Evidence quality is ${intelligence.evidence_quality}.`,
          ]
        : []
    ),
    ...failedChecks.map(
      (check) =>
        check.reason ||
        `${check.name} has not passed.`,
    ),
  ];

  const decision =
    intelligence.trading_readiness ===
      "READY" &&
    graduation.ready &&
    blockers.length === 0
      ? "TRADE READY"
      : "NO TRADE";

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border bg-card",
        decision === "TRADE READY"
          ? "border-emerald-500/25"
          : "border-amber-500/25",
      )}
      data-testid="trading-decision-panel"
    >
      <div className="border-b border-border bg-muted/10 px-5 py-4">
        <div className="flex items-center gap-2">
          <LockKeyhole
            className={cn(
              "h-4 w-4",
              decision === "TRADE READY"
                ? "text-emerald-400"
                : "text-amber-400",
            )}
          />

          <h4 className="text-sm font-medium">
            Today&apos;s Decision
          </h4>
        </div>
      </div>

      <div className="p-5">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p
              className={cn(
                "text-3xl font-bold tracking-tight",
                decision === "TRADE READY"
                  ? "text-emerald-400"
                  : "text-amber-400",
              )}
            >
              {decision}
            </p>

            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              {decision === "TRADE READY"
                ? (
                    "Current intelligence and graduation evidence do not show a deterministic trading blocker."
                  )
                : (
                    "KAIRO is withholding execution because one or more evidence, readiness or graduation requirements remain blocked."
                  )}
            </p>
          </div>

          <div className="rounded-lg border border-border bg-background px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Market Outlook
            </p>

            <p className="mt-1 font-mono text-sm">
              {displayName(
                intelligence.market_outlook,
              )}
            </p>
          </div>
        </div>

        {blockers.length > 0 && (
          <div className="mt-5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Why KAIRO is not trading
            </p>

            <div className="mt-3 grid gap-2 lg:grid-cols-2">
              {blockers.map(
                (blocker) => (
                  <div
                    key={blocker}
                    className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-sm"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />

                    <span className="text-muted-foreground">
                      {blocker}
                    </span>
                  </div>
                ),
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


function RecommendedActionsPanel({
  overview,
}: {
  overview: CopilotOverview;
}) {
  const actions = [
    ...(overview.trading_intelligence
      .trading_readiness !== "READY"
      ? [
          {
            title:
              "Run Intelligence Cycle",
            detail:
              "Refresh current research, signals and readiness evidence.",
          },
        ]
      : []),
    ...(overview.graduation.failed_checks >
    0
      ? [
          {
            title:
              "Review Graduation Report",
            detail:
              `${overview.graduation.failed_checks} graduation requirement(s) remain blocked.`,
          },
        ]
      : []),
    ...(overview.failures.recent_count >
    0
      ? [
          {
            title:
              "Review Failed Jobs",
            detail:
              `${overview.failures.recent_count} recent failure(s) require operational review.`,
          },
        ]
      : []),
    ...(overview.trading_intelligence
      .evidence_quality !== "HIGH"
      ? [
          {
            title:
              "Inspect Latest Research",
            detail:
              `Current evidence quality is ${overview.trading_intelligence.evidence_quality}.`,
          },
        ]
      : []),
  ];

  if (actions.length === 0) {
    actions.push({
      title:
        "Continue Monitoring",
      detail:
        "No deterministic intervention is currently required.",
    });
  }

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center gap-2">
        <PlayCircle className="h-4 w-4 text-[#D4AF37]" />

        <h4 className="text-sm font-medium">
          Recommended Actions
        </h4>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {actions.map(
          (action) => (
            <div
              key={action.title}
              className="flex items-start gap-3 rounded-lg border border-border bg-background p-4"
            >
              <div className="rounded-md border border-[#D4AF37]/20 bg-[#D4AF37]/10 p-2 text-[#D4AF37]">
                <TrendingUp className="h-4 w-4" />
              </div>

              <div>
                <p className="text-sm font-medium">
                  {action.title}
                </p>

                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {action.detail}
                </p>
              </div>
            </div>
          ),
        )}
      </div>
    </div>
  );
}


export function ExecutiveCopilotDashboard({
  overview,
  refreshing,
  onRefresh,
}: {
  overview: CopilotOverview;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const platformHealthy =
    overview.platform.overall_status ===
    "HEALTHY";

  const noFailures =
    overview.failures.recent_count === 0;

  const intelligence =
    overview.trading_intelligence;

  const graduation =
    overview.graduation;

  const readinessHealthy =
    intelligence.trading_readiness ===
    "READY";

  const graduationProgress =
    graduation.total_checks > 0
      ? (
          `${graduation.passed_checks}` +
          ` / ${graduation.total_checks}`
        )
      : "0 / 0";

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-[#D4AF37]" />

            <h3 className="text-sm font-medium">
              Executive Intelligence Dashboard
            </h3>

            <span
              className={cn(
                "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                overview.overall_status ===
                  "HEALTHY"
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-400",
              )}
            >
              {overview.overall_status}
            </span>
          </div>

          <p className="mt-1 text-xs text-muted-foreground">
            Updated{" "}
            {formatTimestamp(
              overview.generated_at,
            )}
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw
            className={cn(
              "mr-2 h-3.5 w-3.5",
              refreshing &&
                "animate-spin",
            )}
          />

          Refresh
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <OverviewMetricCard
          title="Platform Health"
          value={
            platformHealthy
              ? "Healthy"
              : overview.platform
                  .overall_status
          }
          detail={
            `${overview.platform.online_services}` +
            ` of ${overview.platform.required_services}` +
            " required services online."
          }
          icon={Server}
          status={
            platformHealthy
              ? "healthy"
              : "warning"
          }
        />

        <OverviewMetricCard
          title="Trading Readiness"
          value={displayName(
            intelligence
              .trading_readiness,
          )}
          detail={
            `Evidence quality: ` +
            `${displayName(
              intelligence
                .evidence_quality,
            )}.`
          }
          icon={ShieldCheck}
          status={
            readinessHealthy
              ? "healthy"
              : "warning"
          }
        />

        <OverviewMetricCard
          title="Confidence"
          value={confidenceDisplay(
            intelligence.confidence,
          )}
          detail={
            `Market outlook: ` +
            `${displayName(
              intelligence
                .market_outlook,
            )}.`
          }
          icon={CircleGauge}
          status={confidenceStatus(
            intelligence.confidence,
          )}
        />

        <OverviewMetricCard
          title="Actionable Signals"
          value={
            `${intelligence.actionable_signal_count}` +
            ` / ${intelligence.signal_count}`
          }
          detail="Actionable signals versus total current signals."
          icon={Target}
          status={
            intelligence
              .actionable_signal_count >
            0
              ? "healthy"
              : "warning"
          }
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <OverviewMetricCard
          title="Graduation"
          value={
            graduation.ready
              ? "Ready"
              : graduationProgress
          }
          detail={
            graduation.ready
              ? (
                  "All supplied graduation requirements have passed."
                )
              : (
                  `${graduation.failed_checks}` +
                  " requirement(s) remain blocked."
                )
          }
          icon={BarChart3}
          status={
            graduation.ready
              ? "healthy"
              : "warning"
          }
        />

        <OverviewMetricCard
          title="Current Activity"
          value={String(
            overview.activity.active_jobs,
          )}
          detail={
            `${overview.activity.running_jobs}` +
            " running, " +
            `${overview.activity.queued_jobs}` +
            " queued."
          }
          icon={Activity}
          status={
            overview.activity.active_jobs > 0
              ? "info"
              : "healthy"
          }
        />

        <OverviewMetricCard
          title="Next Automation"
          value={
            overview.schedule
              ? displayName(
                  overview.schedule
                    .task_type,
                )
              : "None"
          }
          detail={
            overview.schedule
              ? (
                  `${formatTimestamp(
                    overview.schedule
                      .next_run_at,
                  )} · ` +
                  relativeTimestamp(
                    overview.schedule
                      .next_run_at,
                  )
                )
              : (
                  "No enabled schedules are configured."
                )
          }
          icon={CalendarClock}
          status={
            overview.schedule
              ? "info"
              : "warning"
          }
        />

        <OverviewMetricCard
          title="Recent Failures"
          value={String(
            overview.failures.recent_count,
          )}
          detail={
            noFailures
              ? "No recent job failures."
              : (
                  overview.failures.latest
                    ?.error_summary ||
                  overview.failures.latest
                    ?.error_code ||
                  "Recent failures require review."
                )
          }
          icon={
            noFailures
              ? CheckCircle2
              : XCircle
          }
          status={
            noFailures
              ? "healthy"
              : "danger"
          }
        />
      </div>

      <TradingDecisionPanel
        overview={overview}
      />

      <RecommendedActionsPanel
        overview={overview}
      />

      {overview.attention_items.length >
        0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />

            <h4 className="text-sm font-medium">
              Operational Attention
            </h4>
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {overview.attention_items.map(
              (item) => (
                <AttentionItemCard
                  key={item.code}
                  item={item}
                />
              ),
            )}
          </div>
        </div>
      )}
    </section>
  );
}
