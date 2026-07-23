import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Info } from "lucide-react";
import {
  ScheduledTask,
  ScheduleWriteRequest,
  SchedulableTaskType,
} from "@/lib/types";

// ─── Timezone list ────────────────────────────────────────────────────────────

const PRIORITY_TZ = ["UTC", "Europe/London", "America/New_York"];

function getTimezoneOptions(): string[] {
  try {
    const all: string[] = (Intl as unknown as { supportedValuesOf?: (k: string) => string[] })
      .supportedValuesOf?.("timeZone") ?? PRIORITY_TZ;
    return all;
  } catch {
    return PRIORITY_TZ;
  }
}

const TIMEZONE_OPTIONS = getTimezoneOptions();

// ─── Task types — never offer paper-trading task types ────────────────────────

const TASK_TYPE_OPTIONS: { value: SchedulableTaskType; label: string }[] = [
  { value: "INTELLIGENCE_CYCLE",   label: "Intelligence Cycle" },
  { value: "NEWS_RESEARCH_CYCLE",  label: "News Research Cycle" },
  { value: "STRATEGY_REPORT",      label: "Strategy Report" },
  { value: "SHADOW_ANALYSIS",      label: "Shadow Analysis" },
];

// ─── Zod schema ───────────────────────────────────────────────────────────────

const VALID_TZ = new Set(TIMEZONE_OPTIONS);

const scheduleSchema = z
  .object({
    task_type: z.enum([
      "INTELLIGENCE_CYCLE",
      "NEWS_RESEARCH_CYCLE",
      "STRATEGY_REPORT",
      "SHADOW_ANALYSIS",
    ] as const),
    enabled: z.boolean().default(true),
    schedule_kind: z.enum(["INTERVAL", "DAILY", "WEEKLY"] as const),
    timezone_name: z.string().refine((tz) => VALID_TZ.has(tz), {
      message: "Invalid timezone",
    }),
    // INTERVAL — entered in minutes by the user, converted to seconds on submit
    interval_minutes: z.coerce.number().int().min(1).optional().nullable(),
    local_hour: z.coerce.number().int().min(0).max(23).optional().nullable(),
    local_minute: z.coerce.number().int().min(0).max(59).optional().nullable(),
    weekday: z.coerce.number().int().min(0).max(6).optional().nullable(),
    catch_up_policy: z.enum(["SKIP", "RUN_ONCE", "RUN_IF_WITHIN_WINDOW"] as const),
    catch_up_window_minutes: z.coerce.number().int().min(1).optional().nullable(),
    // INTELLIGENCE_CYCLE payload fields
    ic_watchlist_path: z.string().optional(),
    ic_provider: z.string().optional(),
    ic_max_price_requests: z.coerce.number().int().min(0).optional().nullable(),
    // NEWS_RESEARCH_CYCLE payload fields
    nr_symbols: z.string().optional(),
    nr_watchlist_path: z.string().optional(),
    nr_provider: z.string().optional(),
    nr_max_price_requests: z.coerce.number().int().min(0).optional().nullable(),
  })
  .superRefine((data, ctx) => {
    if (data.schedule_kind === "INTERVAL" && !data.interval_minutes) {
      ctx.addIssue({ code: "custom", path: ["interval_minutes"], message: "Enter interval in minutes" });
    }
    if (
      (data.schedule_kind === "DAILY" || data.schedule_kind === "WEEKLY") &&
      data.local_hour == null
    ) {
      ctx.addIssue({ code: "custom", path: ["local_hour"], message: "Hour is required" });
    }
    if (
      (data.schedule_kind === "DAILY" || data.schedule_kind === "WEEKLY") &&
      data.local_minute == null
    ) {
      ctx.addIssue({ code: "custom", path: ["local_minute"], message: "Minute is required" });
    }
    if (data.schedule_kind === "WEEKLY" && data.weekday == null) {
      ctx.addIssue({ code: "custom", path: ["weekday"], message: "Day is required" });
    }
    if (
      data.catch_up_policy === "RUN_IF_WITHIN_WINDOW" &&
      !data.catch_up_window_minutes
    ) {
      ctx.addIssue({ code: "custom", path: ["catch_up_window_minutes"], message: "Window is required" });
    }
  });

type FormValues = z.infer<typeof scheduleSchema>;

// ─── Build backend payload from form values ───────────────────────────────────

export function buildPayload(values: FormValues): Record<string, unknown> {
  if (values.task_type === "INTELLIGENCE_CYCLE") {
    const p: Record<string, unknown> = {};
    if (values.ic_watchlist_path?.trim()) p.watchlist_path = values.ic_watchlist_path.trim();
    if (values.ic_provider?.trim()) p.market_data_provider = values.ic_provider.trim().toUpperCase();
    if (values.ic_max_price_requests != null) p.max_price_requests = values.ic_max_price_requests;
    return p;
  }
  if (values.task_type === "NEWS_RESEARCH_CYCLE") {
    const p: Record<string, unknown> = {};
    if (values.nr_symbols?.trim()) {
      p.symbols = values.nr_symbols.split(",").map((s) => s.trim()).filter(Boolean);
    } else if (values.nr_watchlist_path?.trim()) {
      p.watchlist_path = values.nr_watchlist_path.trim();
    }
    if (values.nr_provider?.trim()) p.market_data_provider = values.nr_provider.trim().toUpperCase();
    if (values.nr_max_price_requests != null) p.max_price_requests = values.nr_max_price_requests;
    return p;
  }
  return {};
}

export function buildWriteRequest(values: FormValues): ScheduleWriteRequest {
  const base: ScheduleWriteRequest = {
    task_type: values.task_type,
    enabled: values.enabled,
    schedule_kind: values.schedule_kind,
    timezone_name: values.timezone_name,
    catch_up_policy: values.catch_up_policy,
    payload: buildPayload(values),
  };

  if (values.schedule_kind === "INTERVAL") {
    base.interval_seconds = (values.interval_minutes ?? 0) * 60;
  }
  if (values.schedule_kind === "DAILY" || values.schedule_kind === "WEEKLY") {
    base.local_hour = values.local_hour ?? 0;
    base.local_minute = values.local_minute ?? 0;
  }
  if (values.schedule_kind === "WEEKLY") {
    base.weekday = values.weekday ?? 0;
  }
  if (values.catch_up_policy === "RUN_IF_WITHIN_WINDOW") {
    base.catch_up_window_seconds = (values.catch_up_window_minutes ?? 0) * 60;
  }

  return base;
}

// ─── Default values from existing schedule (edit mode) ───────────────────────

function defaultsFromSchedule(s: ScheduledTask | null): Partial<FormValues> {
  if (!s) return { schedule_kind: "INTERVAL", catch_up_policy: "SKIP", timezone_name: "UTC", enabled: true };
  const pl = s.payload ?? {};
  return {
    task_type: s.task_type,
    enabled: s.enabled,
    schedule_kind: s.schedule_kind,
    timezone_name: s.timezone_name,
    catch_up_policy: s.catch_up_policy,
    interval_minutes: s.interval_seconds ? s.interval_seconds / 60 : null,
    local_hour: s.local_hour,
    local_minute: s.local_minute,
    weekday: s.weekday,
    catch_up_window_minutes: s.catch_up_window_seconds ? s.catch_up_window_seconds / 60 : null,
    ic_watchlist_path: typeof pl.watchlist_path === "string" ? pl.watchlist_path : "",
    ic_provider:
      typeof pl.market_data_provider === "string"
        ? pl.market_data_provider
        : typeof pl.provider === "string"
          ? pl.provider
          : "TWELVE_DATA",
    ic_max_price_requests: typeof pl.max_price_requests === "number" ? pl.max_price_requests : null,
    nr_symbols: Array.isArray(pl.symbols) ? (pl.symbols as string[]).join(", ") : "",
    nr_watchlist_path: typeof pl.watchlist_path === "string" ? pl.watchlist_path : "",
    nr_provider:
      typeof pl.market_data_provider === "string"
        ? pl.market_data_provider
        : typeof pl.provider === "string"
          ? pl.provider
          : "TWELVE_DATA",
    nr_max_price_requests: typeof pl.max_price_requests === "number" ? pl.max_price_requests : null,
  };
}

// ─── Component ────────────────────────────────────────────────────────────────

interface ScheduleFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editSchedule?: ScheduledTask | null;
  onSubmit: (req: ScheduleWriteRequest) => void;
  isPending: boolean;
}

const WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function ScheduleFormDialog({
  open,
  onOpenChange,
  editSchedule,
  onSubmit,
  isPending,
}: ScheduleFormDialogProps) {
  const isEdit = !!editSchedule;

  const form = useForm<FormValues>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: defaultsFromSchedule(editSchedule ?? null),
  });

  // Reset form when the dialog opens or editSchedule changes
  useEffect(() => {
    if (open) {
      form.reset(defaultsFromSchedule(editSchedule ?? null));
    }
  }, [open, editSchedule]); // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleKind = form.watch("schedule_kind");
  const catchUpPolicy = form.watch("catch_up_policy");
  const taskType = form.watch("task_type");

  const handleSubmit = (values: FormValues) => {
    onSubmit(buildWriteRequest(values));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md overflow-y-auto max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Schedule" : "New Schedule"}</DialogTitle>
        </DialogHeader>

        {/* Safety notice */}
        <div className="flex items-start gap-2 px-3 py-2 rounded-md bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
          <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          Research automation only. Paper-trading start and stop remain manual.
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-4"
            data-testid="schedule-form"
          >
            {/* Task type */}
            <FormField
              control={form.control}
              name="task_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                    Task Type
                  </FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-task-type">
                        <SelectValue placeholder="Select task type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TASK_TYPE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Schedule kind */}
            <FormField
              control={form.control}
              name="schedule_kind"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                    Cadence
                  </FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-schedule-kind">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="INTERVAL">Interval (every N minutes)</SelectItem>
                      <SelectItem value="DAILY">Daily (at a specific time)</SelectItem>
                      <SelectItem value="WEEKLY">Weekly (day + time)</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Interval minutes — only for INTERVAL */}
            {scheduleKind === "INTERVAL" && (
              <FormField
                control={form.control}
                name="interval_minutes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                      Interval (minutes)
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        placeholder="60"
                        data-testid="input-interval-minutes"
                        {...field}
                        value={field.value ?? ""}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Weekday — only for WEEKLY */}
            {scheduleKind === "WEEKLY" && (
              <FormField
                control={form.control}
                name="weekday"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                      Day of Week
                    </FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(parseInt(v, 10))}
                      value={field.value?.toString() ?? ""}
                    >
                      <FormControl>
                        <SelectTrigger data-testid="select-weekday">
                          <SelectValue placeholder="Select day" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {WEEKDAY_LABELS.map((d, i) => (
                          <SelectItem key={i} value={String(i)}>
                            {d}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Hour + Minute — DAILY and WEEKLY */}
            {(scheduleKind === "DAILY" || scheduleKind === "WEEKLY") && (
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="local_hour"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Hour (0–23)
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          max={23}
                          placeholder="8"
                          data-testid="input-local-hour"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="local_minute"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Minute (0–59)
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          max={59}
                          placeholder="0"
                          data-testid="input-local-minute"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {/* Timezone */}
            <FormField
              control={form.control}
              name="timezone_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                    Timezone
                  </FormLabel>
                  <Select onValueChange={field.onChange} value={field.value ?? "UTC"}>
                    <FormControl>
                      <SelectTrigger data-testid="select-timezone">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent className="max-h-60">
                      {PRIORITY_TZ.map((tz) => (
                        <SelectItem key={tz} value={tz}>
                          {tz}
                        </SelectItem>
                      ))}
                      <div className="border-t border-border my-1" />
                      {TIMEZONE_OPTIONS.filter((tz) => !PRIORITY_TZ.includes(tz)).map((tz) => (
                        <SelectItem key={tz} value={tz}>
                          {tz}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* ── Task-type-specific payload fields ──────────────────────── */}
            {taskType === "INTELLIGENCE_CYCLE" && (
              <div className="space-y-3 pt-1 border-t border-border">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Intelligence Cycle Parameters
                </p>
                <FormField
                  control={form.control}
                  name="ic_watchlist_path"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Watchlist Path (optional)
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="data/watchlists/us_large_cap.txt"
                          data-testid="input-ic-watchlist"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="ic_provider"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Market Data Provider
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="TWELVE_DATA"
                          data-testid="input-ic-provider"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="ic_max_price_requests"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Max Price Requests (optional)
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          placeholder="5"
                          data-testid="input-ic-max-price"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {taskType === "NEWS_RESEARCH_CYCLE" && (
              <div className="space-y-3 pt-1 border-t border-border">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  News Research Parameters
                </p>
                <FormField
                  control={form.control}
                  name="nr_symbols"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Symbols (comma-separated, or leave empty for watchlist)
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="AAPL, MSFT, TSLA"
                          data-testid="input-nr-symbols"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="nr_watchlist_path"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Watchlist Path (optional)
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="data/watchlists/us_large_cap.txt"
                          data-testid="input-nr-watchlist"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="nr_provider"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                        Market Data Provider
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="TWELVE_DATA"
                          data-testid="input-nr-provider"
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {/* Catch-up policy */}
            <FormField
              control={form.control}
              name="catch_up_policy"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                    Catch-Up Policy
                  </FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-catch-up-policy">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="SKIP">Skip missed runs</SelectItem>
                      <SelectItem value="RUN_ONCE">Run once after restart</SelectItem>
                      <SelectItem value="RUN_IF_WITHIN_WINDOW">Run if within time window</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Catch-up window — only for RUN_IF_WITHIN_WINDOW */}
            {catchUpPolicy === "RUN_IF_WITHIN_WINDOW" && (
              <FormField
                control={form.control}
                name="catch_up_window_minutes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground">
                      Catch-Up Window (minutes)
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        placeholder="60"
                        data-testid="input-catch-up-window"
                        {...field}
                        value={field.value ?? ""}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending} data-testid="submit-schedule-form">
                {isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving…
                  </>
                ) : isEdit ? (
                  "Save Changes"
                ) : (
                  "Create Schedule"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
