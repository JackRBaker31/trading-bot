import React, {
  FormEvent,
  useState,
} from "react";

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
  Activity, 
  CalendarClock,
  RefreshCw,
  Server,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  CopilotResponse,
  CopilotSuggestion,
  CopilotSuggestionKind,
  useCopilotQuery,
  useCopilotSuggestions,
  CopilotAttentionItem,
  CopilotOverview,
  useCopilotOverview,
} from "@/hooks/useCopilot";
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

function CopilotSuggestionCard({
  suggestion,
}: {
  suggestion: CopilotSuggestion;
}) {
  const Icon = suggestionIcon(
    suggestion.kind,
  );

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        suggestionClasses(
          suggestion.kind,
        ),
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
  status?:
    | "healthy"
    | "warning"
    | "danger"
    | "info";
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
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            {title}
          </p>

          <p className="mt-2 text-2xl font-semibold">
            {value}
          </p>
        </div>

        <div
          className={cn(
            "rounded-lg border p-2.5",
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


function CopilotOverviewPanel({
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

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-[#D4AF37]" />

            <h3 className="text-sm font-medium">
              Live Intelligence Overview
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

      {overview.attention_items.length >
        0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />

            <h4 className="text-sm font-medium">
              Attention Required
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

  const suggestionsQuery =
    useCopilotSuggestions();

    const overviewQuery =
    useCopilotOverview();

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
            <CopilotOverviewPanel
                overview={overviewQuery.data}
                refreshing={
                overviewQuery.isFetching
                }
                onRefresh={() => {
                void overviewQuery.refetch();
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