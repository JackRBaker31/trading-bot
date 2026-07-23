import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { usePaperTradingStatus } from "@/hooks/usePaperTradingStatus";
import {
  AppStatus,
  ReconciliationStatus,
} from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Loader2,
  Power,
  PowerOff,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

// ─── Status panel helpers ─────────────────────────────────────────────────────

function StatusCell({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <span className="text-muted-foreground uppercase text-[10px] tracking-wider block">
        {label}
      </span>
      <div className="font-mono text-sm">{children}</div>
    </div>
  );
}

function BoolIndicator({
  value,
  trueLabel,
  falseLabel,
  trueIsGood = true,
}: {
  value: boolean | null | undefined;
  trueLabel: string;
  falseLabel: string;
  trueIsGood?: boolean;
}) {
  if (value == null) return <span className="text-muted-foreground text-xs">—</span>;
  const isGood = trueIsGood ? value : !value;
  return (
    <div className="flex items-center gap-1.5">
      {isGood ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
      ) : (
        <XCircle className="w-3.5 h-3.5 text-destructive shrink-0" />
      )}
      <span className={cn("text-xs font-medium", isGood ? "text-emerald-400" : "text-destructive")}>
        {value ? trueLabel : falseLabel}
      </span>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PaperTradingPage() {
  const { data: status, isLoading } = usePaperTradingStatus();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [startOpen, setStartOpen] = useState(false);
  const [stopOpen, setStopOpen] = useState(false);

  // Supplementary status queries for the status panel
  const { data: appStatus } = useQuery({
    queryKey: ["api-status"],
    queryFn: () => apiClient.get<AppStatus>("/status"),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const { data: recon } = useQuery({
    queryKey: ["reconciliation-latest"],
    queryFn: () => apiClient.get<ReconciliationStatus>("/reconciliation/latest"),
    refetchInterval: 30_000,
  });

  // ── Mutations ──────────────────────────────────────────────────────────────
  const startMutation = useMutation({
    mutationFn: () =>
      apiClient.post("/paper-trading/start", {
        confirm_demo_paper_trading: true,
      }),
    onSuccess: () => {
      setStartOpen(false);
      queryClient.invalidateQueries({ queryKey: ["paper-trading-status"] });
      toast({ title: "Paper trading starting", description: "Worker is initializing." });
    },
    onError: (err: Error) => {
      toast({ variant: "destructive", title: "Failed to start", description: err.message });
    },
  });

  const stopMutation = useMutation({
    mutationFn: () =>
      apiClient.post("/paper-trading/stop", { confirm_stop: true }),
    onSuccess: () => {
      setStopOpen(false);
      queryClient.invalidateQueries({ queryKey: ["paper-trading-status"] });
      toast({ title: "Stop requested", description: "Worker will complete its current cycle before stopping." });
    },
    onError: (err: Error) => {
      toast({ variant: "destructive", title: "Failed to stop", description: err.message });
    },
  });

  // ── State derivation ──────────────────────────────────────────────────────
  const isStopped = !status || status.state === "STOPPED";
  const isRunning = status?.state === "RUNNING";
  const isTransitioning =
    status?.state === "STARTING" || status?.state === "STOP_REQUESTED";

  const unresolvedCount = recon?.unresolved_order_count ?? appStatus?.unresolved_order_count ?? null;
  const reconSafe = recon?.safe_to_start ?? null;

  return (
    <div className="space-y-6 max-w-3xl mx-auto mt-6">
      {/* ── Demo mode banner ────────────────────────────────────────────────── */}
      <div className="bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37] p-4 rounded-lg flex items-center justify-center gap-3">
        <ShieldAlert className="w-5 h-5 shrink-0" />
        <span className="font-bold tracking-widest uppercase text-sm">
          DEMO PAPER TRADING — REAL-MONEY TRADING DISABLED
        </span>
      </div>

      {/* ── Worker control ──────────────────────────────────────────────────── */}
      <Card className="border-border shadow-xl">
        <CardHeader className="text-center pb-6 pt-8">
          <CardTitle className="text-xl font-light uppercase tracking-[0.2em] mb-1 text-muted-foreground">
            Worker Control
          </CardTitle>
          <div className="flex justify-center mt-5">
            {isLoading ? (
              <Skeleton className="h-10 w-48 rounded-full" />
            ) : (
              <div className="scale-150 transform origin-center" data-testid="status-worker-state">
                <StatusBadge status={status?.state || "UNKNOWN"} className="px-4 py-1 text-sm" />
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-8 pb-8">
          {/* ── Status panel ────────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 border-t border-b py-6 max-w-lg mx-auto">
            <StatusCell label="Process ID">
              {status?.process_id ?? "—"}
            </StatusCell>
            <StatusCell label="Lock Present">
              <BoolIndicator
                value={status?.lock_present}
                trueLabel="YES"
                falseLabel="NO"
                trueIsGood={false}
              />
            </StatusCell>
            <StatusCell label="Stop Requested">
              <BoolIndicator
                value={status?.stop_requested}
                trueLabel="YES"
                falseLabel="NO"
                trueIsGood={false}
              />
            </StatusCell>
            <StatusCell label="Broker Environment">
              {appStatus ? (
                <span className="text-[#D4AF37] text-xs font-bold uppercase">
                  {appStatus.broker_environment}
                </span>
              ) : "—"}
            </StatusCell>
            <StatusCell label="Market Data">
              <span className="text-xs">{appStatus?.market_data_provider ?? "—"}</span>
            </StatusCell>
            <StatusCell label="Execution Perm.">
              <BoolIndicator
                value={appStatus?.execution_permission_confirmed}
                trueLabel="Confirmed"
                falseLabel="Not confirmed"
              />
            </StatusCell>
            <StatusCell label="Real-Money Trading">
              <BoolIndicator
                value={appStatus?.real_money_trading_enabled ?? false}
                trueLabel="ENABLED ⚠"
                falseLabel="Disabled ✓"
                trueIsGood={false}
              />
            </StatusCell>
            <StatusCell label="Reconciliation">
              {reconSafe === null ? (
                <span className="text-muted-foreground text-xs">—</span>
              ) : (
                <BoolIndicator
                  value={reconSafe}
                  trueLabel="Safe to start"
                  falseLabel="Not safe"
                />
              )}
            </StatusCell>
            <StatusCell label="Unresolved Orders">
              {unresolvedCount === null ? (
                <span className="text-muted-foreground text-xs">—</span>
              ) : unresolvedCount > 0 ? (
                <span className="flex items-center gap-1.5 text-amber-400 text-xs font-medium">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  {unresolvedCount}
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  None
                </span>
              )}
            </StatusCell>
          </div>

          {/* ── Action buttons ─────────────────────────────────────────────── */}
          <div className="flex justify-center gap-4">
            {isStopped && (
              <Button
                size="lg"
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-[0_0_20px_rgba(5,150,105,0.2)] px-6"
                onClick={() => setStartOpen(true)}
                disabled={isTransitioning}
                data-testid="button-start"
              >
                <Power className="w-4 h-4 mr-2" />
                Start DEMO Paper Trading
              </Button>
            )}

            {isRunning && (
              <Button
                size="lg"
                variant="destructive"
                className="shadow-[0_0_20px_rgba(220,38,38,0.2)] px-6"
                onClick={() => setStopOpen(true)}
                disabled={isTransitioning}
                data-testid="button-stop"
              >
                <PowerOff className="w-4 h-4 mr-2" />
                Request Graceful Stop
              </Button>
            )}

            {isTransitioning && (
              <Button size="lg" disabled variant="outline" className="px-6">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {status?.state === "STARTING" ? "Starting…" : "Stopping…"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* ── Start confirmation dialog ────────────────────────────────────────── */}
      <Dialog open={startOpen} onOpenChange={setStartOpen}>
        <DialogContent data-testid="dialog-confirm-start">
          <DialogHeader>
            <DialogTitle className="uppercase tracking-wider">
              Start DEMO Paper Trading
            </DialogTitle>
            <DialogDescription className="text-base py-4 text-foreground/90 font-medium leading-relaxed">
              This will start automatic Trading 212 DEMO paper trading. Real-money
              trading remains disabled.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStartOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {startMutation.isPending && (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              )}
              Confirm Start
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Stop confirmation dialog ────────────────────────────────────────── */}
      <Dialog open={stopOpen} onOpenChange={setStopOpen}>
        <DialogContent data-testid="dialog-confirm-stop">
          <DialogHeader>
            <DialogTitle className="uppercase tracking-wider">
              Request Graceful Stop
            </DialogTitle>
            <DialogDescription className="text-base py-4 text-foreground/90 font-medium leading-relaxed">
              The worker will complete its current cycle before stopping.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStopOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => stopMutation.mutate()}
              disabled={stopMutation.isPending}
            >
              {stopMutation.isPending && (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              )}
              Confirm Stop
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
