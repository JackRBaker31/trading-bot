import React, {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  useIntelligenceHealth,
} from "@/hooks/useIntelligenceObservability";

import {
  useAdvancedIntelligence,
} from "@/hooks/useAdvancedIntelligence";

import {
  useAdaptiveIntelligence,
  useProposeStrategyEvolution,
} from "@/hooks/useAdaptiveIntelligence";

import {
  useCaptureDecisionOutcomes,
  useDecisionOutcomes,
} from "@/hooks/useDecisionOutcomes";

import {
  useDecisionMemory,
} from "@/hooks/useDecisionMemory";

import {
  useMacroAnalysis,
} from "@/hooks/useMacroAnalysis";

import {
  useTechnicalAnalysis,
} from "@/hooks/useTechnicalAnalysis";

import {
  useInvestmentTheses,
} from "@/hooks/useInvestmentTheses";

import {
  useDecisionIntelligence,
} from "@/hooks/useDecisionIntelligence";

import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  CircleHelp,
  Clock3,
  Info,
  Loader2,
  MessageSquareText,
  Send,
  ShieldCheck,
  Sparkles,
  WandSparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  CopilotResponse,
  CopilotSuggestion,
  CopilotSuggestionKind,
  useCopilotChangeSummary,
  useCopilotOverview,
  useLatestDecisionTrace,
  useSymbolDecisions,
  useSymbolDecisionChangeSummary,
  useCopilotQuery,
  useCopilotSuggestions,
} from "@/hooks/useCopilot";
import {
  ExecutiveCopilotDashboard,
} from "@/components/copilot/ExecutiveCopilotDashboard";
import {
  DecisionTimelinePanel,
} from "@/components/copilot/DecisionTimelinePanel";
import {
  DecisionIntelligencePanel,
} from "@/components/copilot/DecisionIntelligencePanel";
import {
  InvestmentThesisPanel,
} from "@/components/copilot/InvestmentThesisPanel";
import {
  DecisionMemoryPanel,
} from "@/components/copilot/DecisionMemoryPanel";
import {
  DecisionOutcomePanel,
} from "@/components/copilot/DecisionOutcomePanel";
import {
  AdaptiveIntelligencePanel,
} from "@/components/copilot/AdaptiveIntelligencePanel";
import {
  AdvancedIntelligencePanel,
} from "@/components/copilot/AdvancedIntelligencePanel";
import {
  IntelligenceHealthPanel,
} from "@/components/copilot/IntelligenceHealthPanel";
import {
  TechnicalAnalysisPanel,
} from "@/components/copilot/TechnicalAnalysisPanel";
import {
  MacroAnalysisPanel,
} from "@/components/copilot/MacroAnalysisPanel";
import {
  SymbolDecisionPanel,
} from "@/components/copilot/SymbolDecisionPanel";
import {
  SymbolDecisionHistoryPanel,
} from "@/components/copilot/SymbolDecisionHistoryPanel";
import {
  ChangeIntelligencePanel,
} from "@/components/copilot/ChangeIntelligencePanel";
import { cn } from "@/lib/utils";


interface ConversationEntry {
  id: number;
  question: string;
  response: CopilotResponse;
}


function suggestionClasses(
  kind: CopilotSuggestionKind,
): string {
  if (kind === "success") {
    return (
      "border-emerald-500/25 " +
      "bg-emerald-500/5"
    );
  }

  if (kind === "warning") {
    return (
      "border-amber-500/30 " +
      "bg-amber-500/5"
    );
  }

  if (kind === "action") {
    return (
      "border-[#D4AF37]/30 " +
      "bg-[#D4AF37]/5"
    );
  }

  return (
    "border-primary/20 " +
    "bg-primary/5"
  );
}


function suggestionIcon(
  kind: CopilotSuggestionKind,
) {
  if (kind === "success") {
    return CheckCircle2;
  }

  if (kind === "warning") {
    return AlertTriangle;
  }

  if (kind === "action") {
    return WandSparkles;
  }

  return Info;
}


function CopilotSuggestionCard({
  suggestion,
}: {
  suggestion: CopilotSuggestion;
}) {
  const Icon =
    suggestion.kind === "success"
      ? CheckCircle2
      : suggestion.kind === "warning"
        ? AlertTriangle
        : suggestion.kind === "action"
          ? WandSparkles
          : Info;

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        suggestion.kind === "success" &&
          "border-emerald-500/25 bg-emerald-500/5",
        suggestion.kind === "warning" &&
          "border-amber-500/30 bg-amber-500/5",
        suggestion.kind === "action" &&
          "border-[#D4AF37]/30 bg-[#D4AF37]/5",
        suggestion.kind === "info" &&
          "border-primary/20 bg-primary/5",
      )}
      data-testid="copilot-suggestion-card"
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "mt-0.5 rounded-md border p-2",
            suggestion.kind === "success" &&
              "border-emerald-500/20 text-emerald-400",
            suggestion.kind === "warning" &&
              "border-amber-500/20 text-amber-400",
            suggestion.kind === "action" &&
              "border-[#D4AF37]/20 text-[#D4AF37]",
            suggestion.kind === "info" &&
              "border-primary/20 text-primary",
          )}
        >
          <Icon className="h-4 w-4" />
        </div>

        <div className="min-w-0">
          <p className="text-sm font-medium">
            {suggestion.title}
          </p>

          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
            {suggestion.message}
          </p>
        </div>
      </div>
    </div>
  );
}


function AnswerPanel({
  entry,
}: {
  entry: ConversationEntry;
}) {
  return (
    <article
      className="overflow-hidden rounded-xl border border-border bg-card"
      data-testid="copilot-answer"
    >
      <div className="border-b border-border bg-muted/10 px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-border bg-background p-2">
            <MessageSquareText className="h-4 w-4 text-muted-foreground" />
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              You asked
            </p>

            <p className="mt-1 text-sm font-medium">
              {entry.question}
            </p>
          </div>
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-[#D4AF37]/30 bg-[#D4AF37]/10 p-2">
            <Bot className="h-5 w-5 text-[#D4AF37]" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#D4AF37]">
                KAIRO response
              </p>

              <span className="rounded-full border border-primary/20 bg-primary/5 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-primary">
                Grounded
              </span>
            </div>

            <p className="mt-2 text-base leading-relaxed">
              {entry.response.summary}
            </p>
          </div>
        </div>

        {entry.response.suggestions.length > 0 && (
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {entry.response.suggestions.map(
              (
                suggestion,
                index,
              ) => (
                <CopilotSuggestionCard
                  key={
                    `${suggestion.title}-` +
                    `${index}`
                  }
                  suggestion={suggestion}
                />
              ),
            )}
          </div>
        )}

        <div className="mt-5 flex items-center gap-2 border-t border-border pt-4 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />

          <span>
            Generated from KAIRO infrastructure,
            job and scheduler evidence.
          </span>
        </div>
      </div>
    </article>
  );
}


export default function CopilotPage() {
  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    conversation,
    setConversation,
  ] = useState<ConversationEntry[]>(
    [],
  );

  const [
    nextEntryId,
    setNextEntryId,
  ] = useState(1);

  useEffect(() => {
    const prefilled = new URLSearchParams(
      window.location.search,
    ).get("question");

    if (prefilled) {
      setQuestion(prefilled.slice(0, 500));
    }
  }, []);

  const suggestionsQuery =
    useCopilotSuggestions();

  const overviewQuery =
    useCopilotOverview();

  const decisionIntelligenceQuery =
    useDecisionIntelligence();

  const investmentThesesQuery =
    useInvestmentTheses();

  const decisionMemoryQuery =
    useDecisionMemory();

  const decisionOutcomesQuery =
    useDecisionOutcomes();

  const adaptiveIntelligenceQuery =
    useAdaptiveIntelligence();

  const advancedIntelligenceQuery =
    useAdvancedIntelligence();

  const intelligenceHealthQuery =
    useIntelligenceHealth();

  const proposeStrategyEvolution =
    useProposeStrategyEvolution();

  const captureDecisionOutcomes =
    useCaptureDecisionOutcomes();

  const technicalSymbol =
    investmentThesesQuery.data?.theses[0]?.symbol ?? null;

  const technicalAnalysisQuery =
    useTechnicalAnalysis(
      technicalSymbol,
    );

  const macroAnalysisQuery =
    useMacroAnalysis();

  const decisionTraceQuery =
    useLatestDecisionTrace();

  const symbolDecisionsQuery =
    useSymbolDecisions();

  const selectedHistorySymbol =
    symbolDecisionsQuery.data?.items[0]?.symbol ?? null;

  const symbolDecisionChangeQuery =
    useSymbolDecisionChangeSummary(
      selectedHistorySymbol,
    );

  const changeSummaryQuery =
    useCopilotChangeSummary();

  const copilotQuery =
    useCopilotQuery();

  async function askQuestion(
    value: string,
  ): Promise<void> {
    const cleaned = value
      .trim()
      .split(/\s+/)
      .join(" ");

    if (
      !cleaned ||
      copilotQuery.isPending
    ) {
      return;
    }

    try {
      const response =
        await copilotQuery.mutateAsync(
          cleaned,
        );

      setConversation(
        (
          current,
        ) => [
          {
            id: nextEntryId,
            question: cleaned,
            response,
          },
          ...current,
        ],
      );

      setNextEntryId(
        (
          current,
        ) => current + 1,
      );

      setQuestion("");
    } catch {
      // The mutation error is rendered below.
    }
  }

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): void {
    event.preventDefault();

    void askQuestion(
      question,
    );
  }

  const suggestions =
    suggestionsQuery.data?.items ?? [];

  return (
    <div className="space-y-6 p-8">
      <section className="relative overflow-hidden rounded-xl border border-border bg-card">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.08),transparent_40%)]" />

        <div className="relative p-6">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="flex items-start gap-4">
              <div className="rounded-xl border border-[#D4AF37]/30 bg-[#D4AF37]/10 p-3">
                <Bot className="h-7 w-7 text-[#D4AF37]" />
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-2xl font-semibold tracking-tight">
                    KAIRO Copilot
                  </h2>

                  <span className="rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#D4AF37]">
                    Grounded v1
                  </span>
                </div>

                <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                  Ask KAIRO about platform health,
                  recent failures, active jobs and
                  upcoming scheduled operations.
                  Responses are generated from the
                  platform&apos;s own operational
                  evidence.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />

              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                  Read-only
                </p>

                <p className="text-xs text-muted-foreground">
                  Cannot place trades or change settings
                </p>
              </div>
            </div>
          </div>

          <form
            className="mt-7 flex flex-col gap-3 sm:flex-row"
            onSubmit={handleSubmit}
          >
            <div className="relative flex-1">
              <Sparkles className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#D4AF37]" />

              <Input
                value={question}
                onChange={(
                  event,
                ) => {
                  setQuestion(
                    event.target.value,
                  );
                }}
                placeholder="Ask KAIRO what is happening and why..."
                className="h-12 pl-11"
                maxLength={500}
                data-testid="copilot-question"
              />
            </div>

            <Button
              type="submit"
              disabled={
                !question.trim() ||
                copilotQuery.isPending
              }
              className="h-12 min-w-[120px]"
              data-testid="copilot-submit"
            >
              {copilotQuery.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Send className="mr-2 h-4 w-4" />
              )}

              {copilotQuery.isPending
                ? "Thinking"
                : "Ask KAIRO"}
            </Button>
          </form>

          {suggestionsQuery.isPending && (
            <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />

              Loading suggested questions...
            </div>
          )}

          {suggestions.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Suggested questions
              </p>

              <div className="flex flex-wrap gap-2">
                {suggestions.map(
                  (
                    item,
                  ) => (
                    <button
                      key={item}
                      type="button"
                      disabled={
                        copilotQuery.isPending
                      }
                      onClick={() => {
                        void askQuestion(
                          item,
                        );
                      }}
                      className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-[#D4AF37]/40 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {item}
                    </button>
                  ),
                )}
              </div>
            </div>
          )}

          {copilotQuery.isError && (
            <div className="mt-4 flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />

              <div>
                <p className="font-medium">
                  Copilot request failed
                </p>

                <p className="mt-1">
                  {copilotQuery.error.message}
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

            {overviewQuery.isPending && (
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {Array.from({
                length: 4,
                }).map((_, index) => (
                <div
                    key={index}
                    className="h-36 animate-pulse rounded-xl border border-border bg-card"
                />
                ))}
            </section>
            )}

            {overviewQuery.isError && (
            <section className="rounded-xl border border-destructive/30 bg-destructive/10 p-5">
                <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 text-destructive" />

                <div>
                    <h3 className="text-sm font-medium text-destructive">
                    Intelligence overview unavailable
                    </h3>

                    <p className="mt-1 text-sm text-muted-foreground">
                    {overviewQuery.error.message}
                    </p>

                    <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={() => {
                        void overviewQuery.refetch();
                    }}
                    >
                    Retry
                    </Button>
                </div>
                </div>
            </section>
            )}

            {overviewQuery.data && (
            <ExecutiveCopilotDashboard
                overview={overviewQuery.data}
                refreshing={
                overviewQuery.isFetching
                }
                onRefresh={() => {
                void overviewQuery.refetch();
                }}
            />
            )}

            {changeSummaryQuery.data && (
              <ChangeIntelligencePanel
                summary={changeSummaryQuery.data}
                refreshing={changeSummaryQuery.isFetching}
                onRefresh={() => {
                  void changeSummaryQuery.refetch();
                }}
              />
            )}


            {symbolDecisionsQuery.data && (
              <SymbolDecisionPanel
                traces={
                  symbolDecisionsQuery
                    .data.items
                }
                refreshing={
                  symbolDecisionsQuery
                    .isFetching
                }
                onRefresh={() => {
                  void symbolDecisionsQuery
                    .refetch();
                }}
              />
            )}


            {symbolDecisionChangeQuery
              .data?.available &&
              symbolDecisionChangeQuery
                .data.summary && (
              <SymbolDecisionHistoryPanel
                summary={
                  symbolDecisionChangeQuery
                    .data.summary
                }
                refreshing={
                  symbolDecisionChangeQuery
                    .isFetching
                }
                onRefresh={() => {
                  void symbolDecisionChangeQuery
                    .refetch();
                }}
              />
            )}


      {conversation.length === 0 ? (
        <section>
          <div className="mb-3 flex items-center gap-2">
            <CircleHelp className="h-4 w-4 text-muted-foreground" />

            <h3 className="text-sm font-medium">
              What Copilot can currently explain
            </h3>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-border bg-card p-5">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />

              <h4 className="mt-3 text-sm font-medium">
                Platform health
              </h4>

              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                Supervisor, API, storage, worker
                and scheduler availability.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-5">
              <AlertTriangle className="h-5 w-5 text-amber-400" />

              <h4 className="mt-3 text-sm font-medium">
                Recent failures
              </h4>

              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                Failed jobs and their recorded
                error summaries.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-5">
              <Clock3 className="h-5 w-5 text-primary" />

              <h4 className="mt-3 text-sm font-medium">
                Current activity
              </h4>

              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                Running and queued background
                operations.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card p-5">
              <WandSparkles className="h-5 w-5 text-[#D4AF37]" />

              <h4 className="mt-3 text-sm font-medium">
                Upcoming work
              </h4>

              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                Enabled schedules and the next
                planned operation.
              </p>
            </div>
          </div>
        </section>
      ) : (
        <section className="space-y-5">
          <div className="flex items-center gap-2">
            <MessageSquareText className="h-4 w-4 text-muted-foreground" />

            <h3 className="text-sm font-medium">
              Conversation
            </h3>
          </div>

          {decisionTraceQuery.data && (
            <DecisionTimelinePanel
              trace={
                decisionTraceQuery.data
              }
              refreshing={
                decisionTraceQuery.isFetching
              }
              onRefresh={() => {
                void decisionTraceQuery.refetch();
              }}
            />
          )}

          {decisionIntelligenceQuery.data && (
            <DecisionIntelligencePanel
              report={
                decisionIntelligenceQuery.data
              }
              refreshing={
                decisionIntelligenceQuery
                  .isFetching
              }
              onRefresh={() => {
                void decisionIntelligenceQuery
                  .refetch();
              }}
            />
          )}

          {investmentThesesQuery.data && (
            <InvestmentThesisPanel
              report={
                investmentThesesQuery.data
              }
              refreshing={
                investmentThesesQuery
                  .isFetching
              }
              onRefresh={() => {
                void investmentThesesQuery
                  .refetch();
              }}
            />
          )}

          {technicalAnalysisQuery.data && (
            <TechnicalAnalysisPanel
              analysis={
                technicalAnalysisQuery.data
              }
              refreshing={
                technicalAnalysisQuery
                  .isFetching
              }
              onRefresh={() => {
                void technicalAnalysisQuery
                  .refetch();
              }}
            />
          )}

          {macroAnalysisQuery.data && (
            <MacroAnalysisPanel
              analysis={
                macroAnalysisQuery.data
              }
              refreshing={
                macroAnalysisQuery
                  .isFetching
              }
              onRefresh={() => {
                void macroAnalysisQuery
                  .refetch();
              }}
            />
          )}

          {decisionMemoryQuery.data && (
            <DecisionMemoryPanel
              overview={
                decisionMemoryQuery.data
              }
              refreshing={
                decisionMemoryQuery
                  .isFetching
              }
              onRefresh={() => {
                void decisionMemoryQuery
                  .refetch();
              }}
            />
          )}

          {decisionOutcomesQuery.data && (
            <DecisionOutcomePanel
              overview={
                decisionOutcomesQuery.data
              }
              refreshing={
                decisionOutcomesQuery
                  .isFetching
              }
              capturing={
                captureDecisionOutcomes
                  .isPending
              }
              onRefresh={() => {
                void decisionOutcomesQuery
                  .refetch();
              }}
              onCapture={() => {
                captureDecisionOutcomes
                  .mutate();
              }}
            />
          )}

          {adaptiveIntelligenceQuery.data && (
            <AdaptiveIntelligencePanel
              report={
                adaptiveIntelligenceQuery.data
              }
              refreshing={
                adaptiveIntelligenceQuery
                  .isFetching
              }
              proposing={
                proposeStrategyEvolution
                  .isPending
              }
              onRefresh={() => {
                void adaptiveIntelligenceQuery
                  .refetch();
              }}
              onPropose={() => {
                proposeStrategyEvolution
                  .mutate();
              }}
            />
          )}

          {advancedIntelligenceQuery.data && (
            <AdvancedIntelligencePanel
              report={
                advancedIntelligenceQuery.data
              }
              refreshing={
                advancedIntelligenceQuery
                  .isFetching
              }
              onRefresh={() => {
                void advancedIntelligenceQuery
                  .refetch();
              }}
            />
          )}

          {intelligenceHealthQuery.data && (
            <IntelligenceHealthPanel
              overview={
                intelligenceHealthQuery.data
              }
              refreshing={
                intelligenceHealthQuery
                  .isFetching
              }
              onRefresh={() => {
                void intelligenceHealthQuery
                  .refetch();
              }}
            />
          )}

          {conversation.map(
            (
              entry,
            ) => (
              <AnswerPanel
                key={entry.id}
                entry={entry}
              />
            ),
          )}
        </section>
      )}
    </div>
  );
}