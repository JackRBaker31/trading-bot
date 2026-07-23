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
import { Loader2, Play, AlertCircle, Newspaper, Database } from "lucide-react";
import { cn } from "@/lib/utils";

const RESEARCH_INVALIDATION_KEYS = [
  ["news-signals"],
  ["news-outcomes"],
  ["news-summary"],
  ["intelligence-snapshot"],
  ["intelligence-briefing"],
  ["shadow-performance"],
  ["intelligence-graduation"],
] as const;

const WATCHLIST_OPTIONS = [
  {
    value: "data/watchlists/us_large_cap.txt",
    label: "US Large Cap",
  },
] as const;

const PRICE_REQUEST_OPTIONS = ["0", "5", "10"] as const;

interface RunNewsResearchDialogProps {
  onStarted: (id: string) => void;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

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

  const [marketDataProvider, setMarketDataProvider] =
    useState("TWELVE_DATA");
  const [targetType, setTargetType] =
    useState<"watchlist" | "symbols">("watchlist");
  const [watchlist, setWatchlist] =
    useState("data/watchlists/us_large_cap.txt");
  const [symbolInput, setSymbolInput] = useState("");
  const [maxRequests, setMaxRequests] = useState("5");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.post<{ job_id: string }>("/jobs/news-research", data),
    onSuccess: (data) => {
      onStarted(data.job_id);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      RESEARCH_INVALIDATION_KEYS.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: [...key] });
      });
      setOpen(false);
      setMarketDataProvider("TWELVE_DATA");
      setTargetType("watchlist");
      setWatchlist("data/watchlists/us_large_cap.txt");
      setSymbolInput("");
      setMaxRequests("5");
      setFormError(null);
      setSubmitted(false);
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const symbols = symbolInput
    .split(",")
    .map((symbol) => symbol.trim().toUpperCase())
    .filter(Boolean);

  const symbolsEmpty = targetType === "symbols" && symbols.length === 0;
  const canSubmit = !mutation.isPending && !symbolsEmpty;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitted(true);
    setFormError(null);

    if (symbolsEmpty) {
      setFormError("Enter at least one symbol, for example AAPL or MSFT.");
      return;
    }

    const payload: Record<string, unknown> = {
      market_data_provider: marketDataProvider,
      max_price_requests: Number.parseInt(maxRequests, 10),
    };

    if (targetType === "watchlist") {
      payload.watchlist = watchlist;
    } else {
      payload.symbols = symbols;
    }

    mutation.mutate(payload);
  };

  const dialogContent = (
    <DialogContent className="sm:max-w-[470px]">
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>Run News Research</DialogTitle>
          <DialogDescription>
            Alpha Vantage supplies news articles. Select the market-price
            provider and an approved research target below.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>News Provider</Label>
            <div
              className="flex items-center justify-between rounded-md border border-border bg-muted/20 px-3 py-2"
              data-testid="fixed-news-provider"
            >
              <div className="flex items-center gap-2">
                <Newspaper className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">Alpha Vantage</span>
              </div>
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-400">
                Fixed
              </span>
            </div>
          </div>

          <div className="grid gap-2">
            <Label>Market Data Provider</Label>
            <Select
              value={marketDataProvider}
              onValueChange={setMarketDataProvider}
            >
              <SelectTrigger data-testid="select-market-data-provider">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="TWELVE_DATA">Twelve Data - Live</SelectItem>
                <SelectItem value="SIMULATED">Simulated - Testing</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-[11px] text-muted-foreground">
              Used only for signal price snapshots and outcome tracking.
            </p>
          </div>

          <div className="grid gap-2">
            <Label>Research Target</Label>
            <Select
              value={targetType}
              onValueChange={(value) => {
                setTargetType(value as "watchlist" | "symbols");
                setFormError(null);
              }}
            >
              <SelectTrigger data-testid="select-research-target">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="watchlist">Approved Watchlist</SelectItem>
                <SelectItem value="symbols">Custom Symbols</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {targetType === "watchlist" ? (
            <div className="grid gap-2">
              <Label>Watchlist</Label>
              <Select value={watchlist} onValueChange={setWatchlist}>
                <SelectTrigger data-testid="select-watchlist">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {WATCHLIST_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="font-mono text-[11px] text-muted-foreground">
                {watchlist}
              </p>
            </div>
          ) : (
            <div className="grid gap-2">
              <Label>Symbols</Label>
              <Input
                value={symbolInput}
                onChange={(event) => {
                  setSymbolInput(event.target.value);
                  if (formError) setFormError(null);
                }}
                placeholder="AAPL, MSFT, TSLA"
                className={cn(
                  submitted &&
                    symbolsEmpty &&
                    "border-destructive focus-visible:ring-destructive",
                )}
                data-testid="input-symbols"
              />
            </div>
          )}

          <div className="grid gap-2">
            <Label>Maximum Price Requests</Label>
            <Select value={maxRequests} onValueChange={setMaxRequests}>
              <SelectTrigger data-testid="select-max-price-requests">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PRICE_REQUEST_OPTIONS.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value === "0" ? "0 - No price snapshots" : value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-start gap-2 rounded-md border border-border bg-muted/10 px-3 py-2 text-xs text-muted-foreground">
            <Database className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>
              News research remains observation-only. This job does not place
              trades.
            </span>
          </div>

          {formError && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
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
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
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
          <Play className="mr-2 h-4 w-4" />
          Run News Research
        </Button>
      </DialogTrigger>
      {dialogContent}
    </Dialog>
  );
}
