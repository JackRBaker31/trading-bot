import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { NewsSummary, NewsSignal, NewsOutcome, PagedResponse } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { formatDate, cn, timeAgo } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertCircle,
  Clock,
  TrendingUp,
  Eye,
  CheckSquare2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  X,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

const PAGE_SIZE = 25;

const SENTIMENT_OPTIONS = [
  { value: "POSITIVE", label: "Pos", cls: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  { value: "NEUTRAL",  label: "Neu", cls: "text-muted-foreground border-border bg-muted/30" },
  { value: "NEGATIVE", label: "Neg", cls: "text-destructive border-destructive/30 bg-destructive/10" },
] as const;

const CONFIDENCE_TIERS = [
  { value: "all",    label: "All",      minConf: undefined, maxConf: undefined },
  { value: "high",   label: "≥70%",     minConf: 0.7,       maxConf: undefined },
  { value: "medium", label: "40–70%",   minConf: 0.4,       maxConf: 0.7 },
  { value: "low",    label: "<40%",     minConf: undefined, maxConf: 0.4 },
] as const;

const HORIZON_OPTIONS = ["1d", "3d", "5d", "1w", "2w"];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function sentimentLabel(s: number): "POSITIVE" | "NEUTRAL" | "NEGATIVE" {
  if (s > 0.1) return "POSITIVE";
  if (s < -0.1) return "NEGATIVE";
  return "NEUTRAL";
}

function SentimentBadge({ sentiment }: { sentiment: number }) {
  const lbl = sentimentLabel(sentiment);
  if (lbl === "POSITIVE")
    return (
      <span className="text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded text-xs font-semibold uppercase">
        Positive
      </span>
    );
  if (lbl === "NEGATIVE")
    return (
      <span className="text-destructive bg-destructive/10 px-2 py-0.5 rounded text-xs font-semibold uppercase">
        Negative
      </span>
    );
  return (
    <span className="text-muted-foreground bg-muted px-2 py-0.5 rounded text-xs font-semibold uppercase">
      Neutral
    </span>
  );
}

// ─── Signal Detail Drawer ─────────────────────────────────────────────────────

function SignalDetailDrawer({
  signal,
  onClose,
  allOutcomes,
}: {
  signal: NewsSignal | null;
  onClose: () => void;
  allOutcomes: NewsOutcome[];
}) {
  const { data: shadowResp } = useQuery({
    queryKey: ["shadow-decisions", signal?.article_id],
    queryFn: () =>
      apiClient.get<Record<string, unknown>>(`/shadow-decisions?article_id=${signal!.article_id}&limit=1`),
    enabled: !!signal?.article_id,
  });

  const matchingOutcomes = signal
    ? allOutcomes.filter((o) => o.article_id === signal.article_id)
    : [];

  // The shadow decisions endpoint may return { items: [...] } or a single object
  const rawDecisions = shadowResp?.items as Record<string, unknown>[] | undefined;
  const shadowDecision: Record<string, unknown> | null =
    rawDecisions?.[0] ?? (shadowResp && !shadowResp.items ? (shadowResp as Record<string, unknown>) : null);

  return (
    <Sheet open={!!signal} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        {signal && (
          <>
            <SheetHeader className="mb-6">
              <div className="flex items-center gap-3 flex-wrap">
                <SheetTitle className="text-2xl font-black font-mono text-primary">
                  {signal.symbol}
                </SheetTitle>
                <SentimentBadge sentiment={signal.sentiment} />
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed mt-1">
                {signal.headline}
              </p>
            </SheetHeader>

            <div className="space-y-6">
              {/* Source & timing */}
              <div className="space-y-2">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Source & Timing
                </p>
                {(
                  [
                    { label: "Source",     value: signal.source },
                    { label: "Published",  value: formatDate(signal.published_at) },
                    { label: "Expires",    value: formatDate(signal.expires_at) },
                  ] as { label: string; value: string }[]
                ).map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="font-mono text-xs text-right">{value}</span>
                  </div>
                ))}
              </div>

              {/* Signal metrics grid */}
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                  Signal Metrics
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "Confidence", value: `${(signal.confidence * 100).toFixed(1)}%`, cls: "text-primary" },
                    { label: "Relevance",  value: `${(signal.relevance  * 100).toFixed(1)}%`, cls: "" },
                  ].map(({ label, value, cls }) => (
                    <div key={label} className="p-3 rounded-lg bg-muted/40">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
                      <p className={cn("text-xl font-black font-mono", cls)}>{value}</p>
                    </div>
                  ))}
                  <div className="p-3 rounded-lg bg-muted/40">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Event Type</p>
                    <p className="text-sm font-bold uppercase">{signal.event_type || "—"}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/40">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Material</p>
                    <p className={cn("text-sm font-bold", signal.is_material ? "text-amber-400" : "text-muted-foreground")}>
                      {signal.is_material ? "YES" : "NO"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Reasoning summary */}
              {signal.reasoning_summary && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    Reasoning
                  </p>
                  <p className="text-sm text-foreground leading-relaxed">{signal.reasoning_summary}</p>
                </div>
              )}

              {/* Matching outcomes */}
              {matchingOutcomes.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    Measured Outcomes ({matchingOutcomes.length})
                  </p>
                  <div className="space-y-2">
                    {matchingOutcomes.map((out, i) => (
                      <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                        <span className="text-xs font-mono uppercase text-muted-foreground">
                          {out.horizon_name}
                        </span>
                        <div className="text-right">
                          <span
                            className={cn(
                              "text-sm font-bold font-mono",
                              out.return_percent > 0
                                ? "text-emerald-400"
                                : out.return_percent < 0
                                  ? "text-destructive"
                                  : "text-muted-foreground",
                            )}
                          >
                            {out.return_percent > 0 ? "+" : ""}
                            {out.return_percent.toFixed(2)}%
                          </span>
                          <p className="text-[10px] text-muted-foreground">
                            {out.reference_price.toFixed(2)} → {out.observed_price.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Shadow decision */}
              {shadowDecision && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    Matching Shadow Decision
                  </p>
                  <div className="p-3 rounded-lg bg-muted/30 space-y-1.5">
                    {Object.entries(shadowDecision)
                      .filter(([, v]) => v != null && typeof v !== "object")
                      .slice(0, 10)
                      .map(([k, v]) => (
                        <div key={k} className="flex justify-between items-center text-xs">
                          <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}</span>
                          <span className="font-mono text-right ml-4 truncate max-w-[60%]">{String(v)}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function NewsPage() {
  // ── Filter state ─────────────────────────────────────────────────────────
  const [symbolFilter, setSymbolFilter] = useState("");
  const [sentiments, setSentiments] = useState<string[]>([]);
  const [confidenceTier, setConfidenceTier] = useState<"all" | "high" | "medium" | "low">("all");
  const [materialOnly, setMaterialOnly] = useState(false);
  const [horizonFilter, setHorizonFilter] = useState("");

  // ── Pagination ───────────────────────────────────────────────────────────
  const [signalPage, setSignalPage] = useState(0);
  const [outcomePage, setOutcomePage] = useState(0);

  // ── Drawer ───────────────────────────────────────────────────────────────
  const [selectedSignal, setSelectedSignal] = useState<NewsSignal | null>(null);

  // ── Build query param strings ─────────────────────────────────────────────
  const tier = CONFIDENCE_TIERS.find((t) => t.value === confidenceTier)!;

  const signalParams = useMemo(() => {
    const p = new URLSearchParams();
    p.set("limit", String(PAGE_SIZE));
    p.set("offset", String(signalPage * PAGE_SIZE));
    if (symbolFilter.trim()) p.set("symbol", symbolFilter.trim().toUpperCase());
    if (sentiments.length === 1) p.set("sentiment_label", sentiments[0]);
    if (materialOnly) p.set("is_material", "true");
    if (tier.minConf != null) p.set("min_confidence", String(tier.minConf));
    if (tier.maxConf != null) p.set("max_confidence", String(tier.maxConf));
    return p.toString();
  }, [symbolFilter, sentiments, confidenceTier, materialOnly, signalPage, tier]);

  const outcomeParams = useMemo(() => {
    const p = new URLSearchParams();
    p.set("limit", String(PAGE_SIZE));
    p.set("offset", String(outcomePage * PAGE_SIZE));
    if (symbolFilter.trim()) p.set("symbol", symbolFilter.trim().toUpperCase());
    if (horizonFilter) p.set("horizon", horizonFilter);
    return p.toString();
  }, [symbolFilter, horizonFilter, outcomePage]);

  // ── Queries ───────────────────────────────────────────────────────────────
  const {
    data: summary,
    isLoading: loadingSummary,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["news-summary"],
    queryFn: () => apiClient.get<NewsSummary>("/news/summary"),
    refetchInterval: 30_000,
  });

  const {
    data: signalsResp,
    isLoading: loadingSignals,
    refetch: refetchSignals,
  } = useQuery({
    queryKey: ["news-signals", signalParams],
    queryFn: () => apiClient.get<PagedResponse<NewsSignal>>(`/news/signals?${signalParams}`),
  });

  const { data: outcomesResp, isLoading: loadingOutcomes } = useQuery({
    queryKey: ["news-outcomes", outcomeParams],
    queryFn: () => apiClient.get<PagedResponse<NewsOutcome>>(`/news/outcomes?${outcomeParams}`),
  });

  // ── Derived state ─────────────────────────────────────────────────────────
  const allSignals  = signalsResp?.items  ?? [];
  const allOutcomes = outcomesResp?.items ?? [];
  const signalTotal  = signalsResp?.total_count  ?? 0;
  const outcomeTotal = outcomesResp?.total_count ?? 0;
  const signalPages  = Math.max(1, Math.ceil(signalTotal  / PAGE_SIZE));
  const outcomePages = Math.max(1, Math.ceil(outcomeTotal / PAGE_SIZE));

  // Client-side sentinel filter (if >1 sentiment selected, backend may not support multi-value)
  const signals = useMemo(() => {
    if (sentiments.length <= 1) return allSignals;
    return allSignals.filter((s) => sentiments.includes(sentimentLabel(s.sentiment)));
  }, [allSignals, sentiments]);

  const lastRefreshAt   = (summary as Record<string, unknown> | undefined)?.last_refresh_at as string | undefined;
  const newestSignalAt  = (summary as Record<string, unknown> | undefined)?.newest_signal_at as string | undefined;

  const hasFilters = !!(symbolFilter || sentiments.length || confidenceTier !== "all" || materialOnly || horizonFilter);

  const toggleSentiment = (s: string) => {
    setSentiments((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
    );
    setSignalPage(0);
  };

  const resetFilters = () => {
    setSymbolFilter("");
    setSentiments([]);
    setConfidenceTier("all");
    setMaterialOnly(false);
    setHorizonFilter("");
    setSignalPage(0);
    setOutcomePage(0);
  };

  const handleRefresh = () => {
    refetchSummary();
    refetchSignals();
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-5 max-w-7xl">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider">
          News & Sentiment Analysis
        </h2>
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
          onClick={handleRefresh}
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          Refresh
        </Button>
      </div>

      {/* ── Freshness banner ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(
          [
            {
              icon: <Clock className="w-3.5 h-3.5 text-muted-foreground" />,
              label: "Last Refresh",
              value: lastRefreshAt ? timeAgo(lastRefreshAt) : "—",
              mono: false,
            },
            {
              icon: <TrendingUp className="w-3.5 h-3.5 text-muted-foreground" />,
              label: "Newest Signal",
              value: newestSignalAt ? timeAgo(newestSignalAt) : "—",
              mono: false,
            },
            {
              icon: <Eye className="w-3.5 h-3.5 text-muted-foreground" />,
              label: "Total Signals",
              value: summary?.total_signals,
              mono: true,
            },
            {
              icon: <CheckSquare2 className="w-3.5 h-3.5 text-muted-foreground" />,
              label: "Measured Outcomes",
              value: summary?.total_outcomes,
              mono: true,
            },
          ] as const
        ).map(({ icon, label, value, mono }) => (
          <div key={label} className="bg-card border border-border rounded-lg p-3">
            <div className="flex items-center gap-1.5 mb-1">
              {icon}
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
            </div>
            {loadingSummary ? (
              <Skeleton className="h-5 w-20" />
            ) : (
              <p className={cn(mono ? "text-xl font-black font-mono text-primary" : "text-sm font-semibold")}>
                {value ?? "—"}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Low-sample warning */}
      {summary && summary.total_signals > 0 && summary.total_signals < 30 && (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-500 text-sm px-4 py-2 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          Only {summary.total_signals} signals — not enough for meaningful statistical conclusions.
        </div>
      )}

      {/* ── Tabs + Filters ────────────────────────────────────────────────── */}
      <Tabs
        defaultValue="signals"
        onValueChange={() => { setSignalPage(0); setOutcomePage(0); }}
      >
        {/* Filter toolbar sits above the tab panels */}
        <div className="flex flex-col gap-3 mb-4">
          {/* Top row: tabs + symbol filter */}
          <div className="flex flex-wrap items-center gap-3">
            <TabsList className="bg-muted/50 border shrink-0">
              <TabsTrigger
                value="signals"
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                Signals ({signalTotal})
              </TabsTrigger>
              <TabsTrigger
                value="outcomes"
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                Outcomes ({outcomeTotal})
              </TabsTrigger>
            </TabsList>
            <Input
              placeholder="Symbol…"
              value={symbolFilter}
              onChange={(e) => {
                setSymbolFilter(e.target.value);
                setSignalPage(0);
                setOutcomePage(0);
              }}
              className="w-28 h-8 text-xs"
            />
          </div>

          {/* Second row: signal-specific filters */}
          <div className="flex flex-wrap gap-1.5 items-center">
            {/* Sentiment chips */}
            {SENTIMENT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => toggleSentiment(opt.value)}
                className={cn(
                  "px-2 py-1 rounded border text-[10px] font-bold uppercase tracking-wide transition-colors",
                  sentiments.includes(opt.value)
                    ? opt.cls
                    : "text-muted-foreground border-border hover:border-muted-foreground/50",
                )}
              >
                {opt.label}
              </button>
            ))}

            <span className="text-border">|</span>

            {/* Confidence tier */}
            {CONFIDENCE_TIERS.map((tier) => (
              <button
                key={tier.value}
                onClick={() => { setConfidenceTier(tier.value); setSignalPage(0); }}
                className={cn(
                  "px-2 py-1 rounded border text-[10px] font-bold uppercase tracking-wide transition-colors",
                  confidenceTier === tier.value
                    ? "bg-primary text-primary-foreground border-primary"
                    : "text-muted-foreground border-border hover:border-muted-foreground/50",
                )}
              >
                {tier.label}
              </button>
            ))}

            <span className="text-border">|</span>

            {/* Material only */}
            <button
              onClick={() => { setMaterialOnly((v) => !v); setSignalPage(0); }}
              className={cn(
                "px-2 py-1 rounded border text-[10px] font-bold uppercase tracking-wide transition-colors",
                materialOnly
                  ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                  : "text-muted-foreground border-border hover:border-muted-foreground/50",
              )}
            >
              Material Only
            </button>

            <span className="text-border">|</span>

            {/* Outcome horizon */}
            {HORIZON_OPTIONS.map((h) => (
              <button
                key={h}
                onClick={() => { setHorizonFilter(horizonFilter === h ? "" : h); setOutcomePage(0); }}
                className={cn(
                  "px-2 py-1 rounded border text-[10px] font-bold uppercase tracking-wide transition-colors",
                  horizonFilter === h
                    ? "bg-primary text-primary-foreground border-primary"
                    : "text-muted-foreground border-border hover:border-muted-foreground/50",
                )}
              >
                {h}
              </button>
            ))}

            {/* Reset */}
            {hasFilters && (
              <>
                <span className="text-border">|</span>
                <button
                  onClick={resetFilters}
                  className="flex items-center gap-1 px-2 py-1 rounded border text-[10px] font-bold uppercase text-muted-foreground border-border hover:text-foreground hover:border-muted-foreground/50 transition-colors"
                >
                  <X className="w-3 h-3" />
                  Reset
                </button>
              </>
            )}
          </div>
        </div>

        {/* ── Signals tab ──────────────────────────────────────────────────── */}
        <TabsContent value="signals" className="m-0">
          <Card>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="w-[130px]">Date</TableHead>
                    <TableHead className="w-[80px]">Symbol</TableHead>
                    <TableHead>Headline</TableHead>
                    <TableHead className="w-[90px]">Sentiment</TableHead>
                    <TableHead className="w-[80px]">Confidence</TableHead>
                    <TableHead className="w-[70px]">Material</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loadingSignals ? (
                    Array.from({ length: 8 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell colSpan={6}>
                          <Skeleton className="h-5 w-full" />
                        </TableCell>
                      </TableRow>
                    ))
                  ) : signals.length > 0 ? (
                    signals.map((sig, i) => (
                      <TableRow
                        key={sig.article_id ?? i}
                        className="cursor-pointer hover:bg-muted/40"
                        onClick={() => setSelectedSignal(sig)}
                      >
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {formatDate(sig.published_at)}
                        </TableCell>
                        <TableCell className="font-bold font-mono text-primary">
                          {sig.symbol}
                        </TableCell>
                        <TableCell
                          className="truncate max-w-xs text-sm"
                          title={sig.headline}
                        >
                          {sig.headline}
                        </TableCell>
                        <TableCell>
                          <SentimentBadge sentiment={sig.sentiment} />
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {(sig.confidence * 100).toFixed(1)}%
                        </TableCell>
                        <TableCell>
                          {sig.is_material ? (
                            <span className="text-amber-400 text-xs font-semibold">YES</span>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        className="h-24 text-center text-muted-foreground text-sm"
                      >
                        {hasFilters ? "No signals match the current filters." : "No signals found."}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
            {signalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                <p className="text-xs text-muted-foreground">
                  Page {signalPage + 1} of {signalPages} · {signalTotal} signals
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSignalPage((p) => Math.max(0, p - 1))}
                    disabled={signalPage === 0}
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSignalPage((p) => Math.min(signalPages - 1, p + 1))}
                    disabled={signalPage >= signalPages - 1}
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* ── Outcomes tab ─────────────────────────────────────────────────── */}
        <TabsContent value="outcomes" className="m-0">
          <Card>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Observed At</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Horizon</TableHead>
                    <TableHead className="text-right">Return %</TableHead>
                    <TableHead className="text-right">Ref Price</TableHead>
                    <TableHead className="text-right">Obs Price</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loadingOutcomes ? (
                    Array.from({ length: 8 }).map((_, i) => (
                      <TableRow key={i}>
                        <TableCell colSpan={6}>
                          <Skeleton className="h-5 w-full" />
                        </TableCell>
                      </TableRow>
                    ))
                  ) : allOutcomes.length > 0 ? (
                    allOutcomes.map((out, i) => (
                      <TableRow key={`${out.article_id}-${out.horizon_name}-${i}`}>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {formatDate(out.observed_at)}
                        </TableCell>
                        <TableCell className="font-bold font-mono text-primary">
                          {out.symbol}
                        </TableCell>
                        <TableCell className="text-xs uppercase font-mono">
                          {out.horizon_name}
                        </TableCell>
                        <TableCell
                          className={cn(
                            "text-right font-mono text-xs",
                            out.return_percent > 0
                              ? "text-emerald-500"
                              : out.return_percent < 0
                                ? "text-destructive"
                                : "text-muted-foreground",
                          )}
                        >
                          {out.return_percent > 0 ? "+" : ""}
                          {out.return_percent.toFixed(2)}%
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-muted-foreground">
                          {out.reference_price.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-muted-foreground">
                          {out.observed_price.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        className="h-24 text-center text-muted-foreground text-sm"
                      >
                        {hasFilters ? "No outcomes match the current filters." : "No outcomes found."}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
            {outcomePages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                <p className="text-xs text-muted-foreground">
                  Page {outcomePage + 1} of {outcomePages} · {outcomeTotal} outcomes
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setOutcomePage((p) => Math.max(0, p - 1))}
                    disabled={outcomePage === 0}
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setOutcomePage((p) => Math.min(outcomePages - 1, p + 1))}
                    disabled={outcomePage >= outcomePages - 1}
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>

      {/* Signal detail drawer */}
      <SignalDetailDrawer
        signal={selectedSignal}
        onClose={() => setSelectedSignal(null)}
        allOutcomes={allOutcomes}
      />
    </div>
  );
}
