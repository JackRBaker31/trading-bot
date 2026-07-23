import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
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
import { Loader2, Play, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

/** Query keys invalidated after a successful news-research job. */
const RESEARCH_INVALIDATION_KEYS = [
  ["news-signals"],
  ["news-outcomes"],
  ["news-summary"],
  ["intelligence-snapshot"],
  ["intelligence-briefing"],
  ["shadow-performance"],
  ["intelligence-graduation"],
] as const;

interface RunNewsResearchDialogProps {
  onStarted: (id: string) => void;
  /** When provided alongside onOpenChange, the dialog is fully controlled — no internal trigger button is rendered. */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

/**
 * Dialog for running a News Research job.
 *
 * Usage (uncontrolled — renders its own trigger button, e.g. on DashboardPage):
 *   <RunNewsResearchDialog onStarted={handleStarted} />
 *
 * Usage (controlled — opened programmatically):
 *   <RunNewsResearchDialog open={open} onOpenChange={setOpen} onStarted={handleStarted} />
 *
 * Source is mutually exclusive: exactly one of `symbols` or `watchlist` is sent.
 * The submit button is disabled when symbols mode is active and no symbols are entered.
 */
export function RunNewsResearchDialog({
  onStarted,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: RunNewsResearchDialogProps) {
  const isControlled =
    controlledOpen !== undefined && controlledOnOpenChange !== undefined;

  const [internalOpen, setInternalOpen] = useState(false);
  const open = isControlled ? controlledOpen : internalOpen;
  const setOpen = isControlled ? controlledOnOpenChange! : setInternalOpen;

  const [provider, setProvider] = useState("TWELVE_DATA");
  const [inputType, setInputType] = useState<"symbols" | "watchlist">("symbols");
  const [inputValue, setInputValue] = useState("");
  const [maxRequests, setMaxRequests] = useState("5");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.post<{ job_id: string }>("/jobs/news-research", data),
    onSuccess: (data) => {
      onStarted(data.job_id);
      // Invalidate jobs list + all downstream intelligence queries
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      RESEARCH_INVALIDATION_KEYS.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: [...key] });
      });
      setOpen(false);
      // Reset form
      setInputValue("");
      setMaxRequests("5");
      setProvider("TWELVE_DATA");
      setInputType("symbols");
      setFormError(null);
      setSubmitted(false);
    },
    onError: (err: Error) => {
      setFormError(err.message);
    },
  });

  const symbols = inputValue
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const symbolsEmpty = inputType === "symbols" && symbols.length === 0;
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
      payload.symbols = symbols;
    } else {
      // watchlist key — backend expects "watchlist", not "watchlist_path"
      payload.watchlist =
        inputValue.trim() || "data/watchlists/us_large_cap.txt";
    }

    mutation.mutate(payload);
  };

  const dialogContent = (
    <DialogContent className="sm:max-w-[425px]">
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>Run News Research</DialogTitle>
          <DialogDescription>
            Fetch news and run AI sentiment analysis. Choose exactly one source:
            specific symbols or a watchlist file.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Provider */}
          <div className="grid gap-2">
            <Label>Provider</Label>
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

          {/* Source type — mutually exclusive */}
          <div className="grid gap-2">
            <Label>Source</Label>
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
                  data-testid={`source-type-${t}`}
                >
                  {t === "symbols" ? "Symbols" : "Watchlist"}
                </button>
              ))}
            </div>
          </div>

          {/* Source value */}
          <div className="grid gap-2">
            <Label>{inputType === "symbols" ? "Symbols" : "Path"}</Label>
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
              className={cn(
                submitted && symbolsEmpty &&
                  "border-destructive focus-visible:ring-destructive",
              )}
              data-testid="input-target"
            />
            {inputType === "watchlist" && !inputValue && (
              <p className="text-[11px] text-muted-foreground">
                Defaults to{" "}
                <span className="font-mono">data/watchlists/us_large_cap.txt</span>
              </p>
            )}
          </div>

          {/* Max price requests */}
          <div className="grid gap-2">
            <Label>Max Price Requests</Label>
            <Input
              type="number"
              value={maxRequests}
              onChange={(e) => setMaxRequests(e.target.value)}
              min="0"
              required
              data-testid="input-max-requests"
            />
          </div>

          {/* Form-level error */}
          {formError && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 px-3 py-2 rounded-md">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{formError}</span>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="submit"
            disabled={!canSubmit}
            data-testid="submit-news-research"
          >
            {mutation.isPending && (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            )}
            Start Job
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );

  if (isControlled) {
    return (
      <Dialog open={open} onOpenChange={setOpen}>
        {dialogContent}
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" data-testid="btn-run-news-research">
          <Play className="w-4 h-4 mr-2" /> Run News Research
        </Button>
      </DialogTrigger>
      {dialogContent}
    </Dialog>
  );
}
