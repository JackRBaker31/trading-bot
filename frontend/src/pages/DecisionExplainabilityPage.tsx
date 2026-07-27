import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  CircleDot,
  Clock3,
  MessageSquareText,
  RefreshCw,
  SearchCheck,
  ShieldCheck,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DecisionScoreComponent,
  InvestmentDecision,
  useDecisionIntelligence,
} from "@/hooks/useDecisionIntelligence";
import {
  SymbolDecisionTrace,
  useSymbolDecisionChangeSummary,
  useSymbolDecisions,
} from "@/hooks/useCopilot";
import { HistoricalSimilarityPanel } from "@/components/decision/HistoricalSimilarityPanel";
import { useHistoricalSimilarity } from "@/hooks/useHistoricalSimilarity";
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

function money(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(value);
}

function recommendationClass(recommendation: string): string {
  if (recommendation === "BUY_CANDIDATE") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
  }
  if (recommendation === "WATCH") {
    return "border-sky-500/30 bg-sky-500/10 text-sky-400";
  }
  if (recommendation === "AVOID") {
    return "border-destructive/30 bg-destructive/10 text-destructive";
  }
  return "border-amber-500/30 bg-amber-500/10 text-amber-400";
}

function executionClass(eligible: boolean): string {
  return eligible
    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
    : "border-amber-500/30 bg-amber-500/10 text-amber-400";
}

function componentPercent(component: DecisionScoreComponent): number {
  if (component.maximum <= 0) return 0;
  return Math.max(0, Math.min(100, (component.value / component.maximum) * 100));
}

function EvidenceList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "warning" | "danger" | "neutral";
}) {
  const Icon =
    tone === "positive"
      ? CheckCircle2
      : tone === "danger"
        ? XCircle
        : tone === "warning"
          ? AlertTriangle
          : CircleDot;

  const iconClass =
    tone === "positive"
      ? "text-emerald-400"
      : tone === "danger"
        ? "text-destructive"
        : tone === "warning"
          ? "text-amber-400"
          : "text-primary";

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

function DecisionList({
  decisions,
  selectedSymbol,
  onSelect,
}: {
  decisions: InvestmentDecision[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}) {
  return (
    <Card className="h-fit">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <TrendingUp className="h-4 w-4 text-primary" />
          Ranked opportunities
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {decisions.map((decision, index) => {
          const selected = decision.symbol === selectedSymbol;
          return (
            <button
              key={decision.symbol}
              type="button"
              className={cn(
                "w-full rounded-lg border p-3 text-left transition-colors",
                selected
                  ? "border-primary/50 bg-primary/10"
                  : "border-border bg-background hover:border-primary/25 hover:bg-muted/30",
              )}
              onClick={() => onSelect(decision.symbol)}
              data-testid={`explain-symbol-${decision.symbol}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold text-muted-foreground">#{index + 1}</span>
                    <span className="font-mono text-sm font-bold text-primary">{decision.symbol}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{decision.headline}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm font-bold">{decision.score.toFixed(1)}</p>
                  <p className="text-[10px] text-muted-foreground">{percentage(decision.confidence)}</p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <span
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                    recommendationClass(decision.recommendation),
                  )}
                >
                  {displayName(decision.recommendation)}
                </span>
                <span
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                    executionClass(decision.eligible_for_execution),
                  )}
                >
                  {decision.eligible_for_execution ? "Executable" : "Blocked"}
                </span>
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}

function DecisionSummary({
  decision,
  trace,
}: {
  decision: InvestmentDecision;
  trace: SymbolDecisionTrace | undefined;
}) {
  const topComponent = [...decision.components].sort(
    (left, right) => componentPercent(right) - componentPercent(left),
  )[0];

  const conclusion = decision.eligible_for_execution
    ? `${decision.symbol} currently passes the recorded execution gates. The strongest scored contributor is ${topComponent?.label ?? "the available evidence"}.`
    : `${decision.symbol} is an advisory ${displayName(decision.recommendation).toLowerCase()} but remains blocked. ${decision.blockers[0] ?? trace?.blockers[0] ?? "Platform execution readiness has not passed."}`;

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.08),transparent_45%)] p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-2xl font-black text-primary">{decision.symbol}</span>
              <span
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
                  recommendationClass(decision.recommendation),
                )}
              >
                {displayName(decision.recommendation)}
              </span>
              <span
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
                  executionClass(decision.eligible_for_execution),
                )}
              >
                {decision.eligible_for_execution ? "Execution eligible" : "Execution blocked"}
              </span>
            </div>
            <h2 className="mt-3 max-w-3xl text-lg font-semibold">{decision.headline}</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {displayName(decision.event_type)} · {displayName(decision.sentiment)} · {displayName(decision.classification)}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-border bg-background/80 p-3 text-right">
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Score</p>
              <p className="mt-1 font-mono text-xl font-bold">{decision.score.toFixed(1)}</p>
            </div>
            <div className="rounded-lg border border-border bg-background/80 p-3 text-right">
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Confidence</p>
              <p className="mt-1 font-mono text-xl font-bold">{percentage(decision.confidence)}</p>
            </div>
            <div className="rounded-lg border border-border bg-background/80 p-3 text-right">
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground">Position</p>
              <p className="mt-1 font-mono text-xl font-bold">{money(decision.suggested_position_value)}</p>
            </div>
          </div>
        </div>
      </div>

      <CardContent className="p-5">
        <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
          <BrainCircuit className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-primary">KAIRO conclusion</p>
            <p className="mt-2 text-sm leading-6">{conclusion}</p>
            {trace?.summary && <p className="mt-2 text-xs leading-5 text-muted-foreground">{trace.summary}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DecisionExplainabilityPage() {
  const decisionQuery = useDecisionIntelligence();
  const traceQuery = useSymbolDecisions();

  const rankedDecisions = useMemo(
    () => [...(decisionQuery.data?.decisions ?? [])].sort((left, right) => right.score - left.score),
    [decisionQuery.data?.decisions],
  );

  const requestedSymbol = useMemo(
    () => new URLSearchParams(window.location.search).get("symbol")?.toUpperCase() ?? "",
    [],
  );

  const [selectedSymbol, setSelectedSymbol] = useState(requestedSymbol);
  const [activeTab, setActiveTab] = useState("score");

  useEffect(() => {
    if (selectedSymbol && rankedDecisions.some((item) => item.symbol === selectedSymbol)) return;
    if (rankedDecisions[0]) setSelectedSymbol(rankedDecisions[0].symbol);
  }, [rankedDecisions, selectedSymbol]);

  const changeQuery = useSymbolDecisionChangeSummary(selectedSymbol || null);
  const similarityQuery = useHistoricalSimilarity(
    selectedSymbol || null,
    activeTab === "history",
  );

  const decision = rankedDecisions.find((item) => item.symbol === selectedSymbol);
  const trace = traceQuery.data?.items.find((item) => item.symbol === selectedSymbol);

  const loading = decisionQuery.isPending || traceQuery.isPending;
  const failed = decisionQuery.isError;

  const askQuestion = encodeURIComponent(
    `Why is ${selectedSymbol || "this symbol"} currently ranked this way, and why is it ${decision?.eligible_for_execution ? "eligible for execution" : "blocked"}?`,
  );

  return (
    <div className="max-w-[1500px] space-y-5 p-8">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary">
            <SearchCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Decision Explainability</h1>
              <span className="rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#D4AF37]">
                v0.7
              </span>
            </div>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              Evidence-backed explanations built from KAIRO&apos;s score components, decision trace,
              execution gates and true historical feature-vector similarity. This page does not alter trading logic.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={decisionQuery.isFetching || traceQuery.isFetching}
            onClick={() => {
              void decisionQuery.refetch();
              void traceQuery.refetch();
              if (activeTab === "history") void similarityQuery.refetch();
              void changeQuery.refetch();
            }}
          >
            <RefreshCw
              className={cn(
                "mr-2 h-4 w-4",
                (decisionQuery.isFetching || traceQuery.isFetching) && "animate-spin",
              )}
            />
            Refresh evidence
          </Button>
          <Button asChild disabled={!selectedSymbol}>
            <Link href={`/copilot?question=${askQuestion}`}>
              <MessageSquareText className="mr-2 h-4 w-4" />
              Ask Copilot
            </Link>
          </Button>
        </div>
      </section>

      {loading && (
        <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
          <Skeleton className="h-[560px]" />
          <div className="space-y-4">
            <Skeleton className="h-64" />
            <Skeleton className="h-96" />
          </div>
        </div>
      )}

      {failed && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="flex items-start gap-3 p-5">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Decision evidence unavailable</p>
              <p className="mt-1 text-sm text-muted-foreground">{decisionQuery.error.message}</p>
              <Button className="mt-3" size="sm" variant="outline" onClick={() => void decisionQuery.refetch()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && !failed && rankedDecisions.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center py-14 text-center">
            <BrainCircuit className="h-8 w-8 text-muted-foreground" />
            <h2 className="mt-4 font-semibold">No ranked decisions available</h2>
            <p className="mt-2 max-w-lg text-sm text-muted-foreground">
              Run an Intelligence Cycle so KAIRO can create current decision evidence.
            </p>
          </CardContent>
        </Card>
      )}

      {!loading && decision && (
        <div className="grid items-start gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
          <DecisionList
            decisions={rankedDecisions}
            selectedSymbol={selectedSymbol}
            onSelect={setSelectedSymbol}
          />

          <div className="min-w-0 space-y-5">
            <DecisionSummary decision={decision} trace={trace} />

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
              <TabsList className="h-auto flex-wrap justify-start">
                <TabsTrigger value="score">Score composition</TabsTrigger>
                <TabsTrigger value="evidence">Evidence & risk</TabsTrigger>
                <TabsTrigger value="timeline">Decision timeline</TabsTrigger>
                <TabsTrigger value="history">Historical similarity</TabsTrigger>
                <TabsTrigger value="change">What changed</TabsTrigger>
              </TabsList>

              <TabsContent value="score" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <BarChart3 className="h-4 w-4 text-primary" />
                      Confidence and score contributors
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-4 lg:grid-cols-2">
                    {decision.components.map((component) => {
                      const contribution = componentPercent(component);
                      return (
                        <div key={component.code} className="rounded-lg border border-border bg-background p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold">{component.label}</p>
                              <p className="mt-1 text-xs leading-5 text-muted-foreground">{component.detail}</p>
                            </div>
                            <span className="whitespace-nowrap font-mono text-sm font-bold">
                              {component.value.toFixed(1)}/{component.maximum.toFixed(0)}
                            </span>
                          </div>
                          <Progress className="mt-4" value={contribution} />
                          <p className="mt-2 text-right text-[10px] text-muted-foreground">
                            {contribution.toFixed(1)}% of available component score
                          </p>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="evidence" className="space-y-4">
                <div className="grid gap-4 lg:grid-cols-2">
                  <EvidenceList title="Supporting evidence" items={decision.reasons} tone="positive" />
                  <EvidenceList title="Warnings" items={decision.warnings} tone="warning" />
                  <EvidenceList
                    title="Execution blockers"
                    items={[...new Set([...decision.blockers, ...(trace?.blockers ?? [])])]}
                    tone="danger"
                  />
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center gap-2 text-sm">
                        <ShieldCheck className="h-4 w-4 text-primary" />
                        Recorded execution state
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3 text-sm">
                      <div className="flex justify-between rounded-md border p-3">
                        <span className="text-muted-foreground">Trading readiness</span>
                        <strong>{displayName(trace?.trading_readiness)}</strong>
                      </div>
                      <div className="flex justify-between rounded-md border p-3">
                        <span className="text-muted-foreground">Graduation</span>
                        <strong>{trace?.graduation_ready ? "Passed" : "Not passed"}</strong>
                      </div>
                      <div className="flex justify-between rounded-md border p-3">
                        <span className="text-muted-foreground">Risk tier</span>
                        <strong>{displayName(decision.risk_tier)}</strong>
                      </div>
                      <div className="flex justify-between rounded-md border p-3">
                        <span className="text-muted-foreground">Execution eligibility</span>
                        <strong>{decision.eligible_for_execution ? "Eligible" : "Blocked"}</strong>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="timeline">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Clock3 className="h-4 w-4 text-primary" />
                      Decision path
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {trace?.stages?.length ? (
                      <div className="space-y-0">
                        {trace.stages.map((stage, index) => {
                          const passed = stage.status === "PASS";
                          const last = index === trace.stages.length - 1;
                          return (
                            <div key={`${stage.sequence}-${stage.stage}`} className="relative flex gap-4">
                              {!last && <div className="absolute left-[15px] top-8 h-[calc(100%-4px)] w-px bg-border" />}
                              <div
                                className={cn(
                                  "relative z-10 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-card",
                                  passed
                                    ? "border-emerald-500/30 text-emerald-400"
                                    : "border-amber-500/30 text-amber-400",
                                )}
                              >
                                {passed ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                              </div>
                              <div className={cn("min-w-0 flex-1 pb-6", last && "pb-0")}>
                                <div className="rounded-lg border border-border bg-background p-4">
                                  <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div>
                                      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                                        {displayName(stage.stage)}
                                      </p>
                                      <p className="mt-1 text-sm font-semibold">{stage.title}</p>
                                    </div>
                                    <span
                                      className={cn(
                                        "rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                                        passed
                                          ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-400"
                                          : "border-amber-500/25 bg-amber-500/10 text-amber-400",
                                      )}
                                    >
                                      {stage.status}
                                    </span>
                                  </div>
                                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{stage.summary}</p>
                                  {stage.evidence.length > 0 && (
                                    <div className="mt-3 space-y-2">
                                      {stage.evidence.map((item) => (
                                        <div key={item} className="flex items-start gap-2 text-xs text-muted-foreground">
                                          <CircleDot className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
                                          <span>{item}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="py-8 text-center text-sm text-muted-foreground">
                        No symbol decision trace is currently available for {decision.symbol}.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="history">
                <HistoricalSimilarityPanel
                  symbol={decision.symbol}
                  report={similarityQuery.data}
                  isPending={similarityQuery.isPending}
                  isError={similarityQuery.isError}
                />
              </TabsContent>

              <TabsContent value="change">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <ArrowRight className="h-4 w-4 text-primary" />
                      What changed since the previous decision
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {changeQuery.isPending ? (
                      <Skeleton className="h-40" />
                    ) : changeQuery.data?.available && changeQuery.data.summary ? (
                      <div className="space-y-4">
                        <p className="rounded-lg border bg-muted/20 p-4 text-sm leading-6">
                          {changeQuery.data.summary.summary}
                        </p>
                        <div className="grid gap-3 sm:grid-cols-3">
                          {[
                            ["Score", changeQuery.data.summary.score_change],
                            ["Confidence", changeQuery.data.summary.confidence_change],
                            ["Rank", changeQuery.data.summary.rank_change],
                          ].map(([label, metric]) => {
                            const typedMetric = metric as typeof changeQuery.data.summary.score_change;
                            return (
                              <div key={label as string} className="rounded-lg border p-4">
                                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label as string}</p>
                                <p className="mt-2 text-lg font-bold">
                                  {typedMetric ? `${typedMetric.change > 0 ? "+" : ""}${typedMetric.change.toFixed(2)}` : "—"}
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">{typedMetric?.direction ?? "No comparison"}</p>
                              </div>
                            );
                          })}
                        </div>
                        <div className="grid gap-4 lg:grid-cols-2">
                          <EvidenceList title="New blockers" items={changeQuery.data.summary.new_blockers} tone="danger" />
                          <EvidenceList title="Cleared blockers" items={changeQuery.data.summary.cleared_blockers} tone="positive" />
                        </div>
                      </div>
                    ) : (
                      <p className="py-8 text-center text-sm text-muted-foreground">
                        A previous comparable decision is not available for {decision.symbol} yet.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      )}
    </div>
  );
}
