import React, { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { Link, useLocation } from "wouter";
import {
  LayoutDashboard,
  Command,
  FlaskConical,
  Newspaper,
  Brain,
  Briefcase,
  ClipboardList,
  ShieldCheck,
  Bot,
  BarChart3,
  Clock,
  ScrollText,
  CalendarClock,
  LogOut,
  WifiOff,
  X,
  Circle,
  User,
  SearchCheck,
  } from "lucide-react";
import { useBackendHealth } from "@/hooks/useBackendHealth";
import { useInfrastructureStatus } from "@/hooks/useInfrastructureStatus";
import { apiClient } from "@/lib/api-client";
import { AppStatus, SupervisorMetadata } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface AppShellProps {
  children: React.ReactNode;
  title: string;
}

const navItems = [
  { icon: Command,                 label: "Operations Centre",     path: "/operations" },
  { icon: Bot,                     label: "KAIRO Copilot",         path: "/copilot",},
  { icon: BarChart3,               label: "Performance Intelligence", path: "/performance" },
  { icon: SearchCheck,              label: "Decision Explainability", path: "/decision-explainability" },
  { icon: LayoutDashboard,         label: "Dashboard",             path: "/dashboard" },
  { icon: FlaskConical,            label: "Research",              path: "/research" },
  { icon: Newspaper,               label: "AI News",               path: "/news" },
  { icon: Brain,                   label: "Shadow Intelligence",   path: "/shadow" },
  { icon: Briefcase,               label: "Portfolio",             path: "/portfolio" },
  { icon: ClipboardList,           label: "Orders",                path: "/orders" },
  { icon: ShieldCheck,             label: "Risk & Reconciliation", path: "/risk" },
  { icon: Bot,                     label: "Paper Trading",         path: "/paper-trading" },
  { icon: Clock,                   label: "Jobs",                  path: "/jobs" },
  { icon: CalendarClock,           label: "Scheduler",             path: "/schedules" },
  { icon: ScrollText,              label: "Audit",                 path: "/audit" },
];

export function AppShell({ children, title }: AppShellProps) {
  const { user, logout } = useAuth();
  const [location] = useLocation();
  const { toast } = useToast();
  const { data: health, isError, isPending } = useBackendHealth();

  // Infrastructure status — already polling at 5 s via the hook
  const { data: infraStatus } = useInfrastructureStatus();

  // App status (provider + mode) — read from shared cache; no new polling
  const { data: appStatus } = useQuery({
    queryKey: ["api-status"],
    queryFn: () => apiClient.get<AppStatus>("/status"),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const isConnected = !!health && !isError;
  const prevConnectedRef = useRef<boolean | null>(null);
  const [bannerVisible, setBannerVisible] = useState(false);

  useEffect(() => {
    if (isPending) return;
    const prev = prevConnectedRef.current;
    prevConnectedRef.current = isConnected;
    if (prev === null) return;
    if (prev && !isConnected) {
      setBannerVisible(true);
    } else if (!prev && isConnected) {
      setBannerVisible(false);
      toast({ title: "Reconnected", description: "Backend connection restored." });
    }
  }, [isConnected, isPending, toast]);

  // ── Derived infra status colour ──────────────────────────────────────────
  const infraDotCls = infraStatus
    ? infraStatus.overall_status === "HEALTHY"
      ? "bg-emerald-500"
      : infraStatus.overall_status === "DEGRADED"
        ? "bg-amber-400"
        : "bg-destructive"
    : "bg-muted-foreground/40";

  const infraLabel = infraStatus?.overall_status ?? "Unknown";

  // ── Supervisor tooltip lines ─────────────────────────────────────────────
  const supSvc = infraStatus?.services?.supervisor;
  const supMeta = supSvc?.metadata as unknown as SupervisorMetadata | undefined;
  const supervisorTooltipLines: string[] = supSvc
    ? [
        `Supervisor: ${supSvc.status}`,
        supMeta?.restart_enabled === true
          ? "Automatic recovery: Enabled"
          : supMeta?.restart_enabled === false
            ? "Automatic recovery: Disabled"
            : null,
        typeof supMeta?.healthy_process_count === "number" &&
        typeof supMeta?.managed_process_count === "number"
          ? `${supMeta.healthy_process_count} of ${supMeta.managed_process_count} managed services healthy`
          : null,
        // Surface degraded/failed/stale supervisor state explicitly
        supSvc.status.toUpperCase() !== "RUNNING"
          ? `⚠ Supervisor ${supSvc.status}`
          : null,
      ].filter((l): l is string => l !== null)
    : [];

  const infraTooltip = [
    `Infrastructure: ${infraLabel}`,
    ...supervisorTooltipLines,
  ].join("\n");

  // ── Provider + mode label ────────────────────────────────────────────────
  const providerLabel = appStatus
    ? `${appStatus.market_data_provider} · ${appStatus.application_mode}`
    : null;

  return (
    <div className="min-h-screen bg-background flex text-foreground">
      {/* ── Sidebar ────────────────────────────────────────────────────────── */}
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col fixed inset-y-0 z-10">
        {/* Logo + demo badge */}
        <div className="p-6">
          <img
            src="/kairo-logo.png"
            alt="Kairo"
            className="w-[190px] object-contain"
          />
          <div className="mt-3">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border border-[#D4AF37]/50 text-[#D4AF37] bg-[#D4AF37]/10 uppercase tracking-wider">
              Demo Platform
            </span>
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location === item.path;
            return (
              <Link
                key={item.path}
                href={item.path}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50",
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 shrink-0",
                    active ? "text-primary" : "text-muted-foreground",
                  )}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User area */}
        <div className="p-4 border-t border-sidebar-border mt-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div
                className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500" : "bg-destructive")}
              />
              <span className="text-xs text-muted-foreground">
                {isConnected ? "System Live" : "Disconnected"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm shrink-0">
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="text-xs text-muted-foreground truncate capitalize">
                {user?.role}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="text-muted-foreground hover:text-destructive shrink-0"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* ── Main content ───────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col pl-64">
        {/* Top bar */}
        <header className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10 px-8 flex items-center justify-between gap-4">
          {/* Page title */}
          <h1 className="text-base font-semibold truncate">{title}</h1>

          {/* Right-side status cluster */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Infrastructure status dot + provider/mode */}
            <div
              className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-card border border-border"
              title={infraTooltip}
            >
              <div className={cn("w-2 h-2 rounded-full shrink-0", infraDotCls)} />
              {providerLabel && (
                <span className="text-[11px] font-mono text-muted-foreground">
                  {providerLabel}
                </span>
              )}
            </div>

            {/* DEMO PAPER TRADING badge */}
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold border border-[#D4AF37]/50 text-[#D4AF37] bg-[#D4AF37]/10 uppercase tracking-wider whitespace-nowrap">
              Demo Paper Trading
            </span>

            {/* Username */}
            {user?.username && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0">
                  {user.username[0].toUpperCase()}
                </div>
                <span className="font-medium max-w-[80px] truncate">
                  {user.username}
                </span>
              </div>
            )}
          </div>
        </header>

        {/* Disconnect banner */}
        {bannerVisible && (
          <div className="bg-destructive/10 border-b border-destructive/30 px-8 py-2.5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5 text-destructive">
              <WifiOff className="w-4 h-4 shrink-0" />
              <span className="text-sm font-medium">
                Backend disconnected — data may be stale
              </span>
            </div>
            <button
              onClick={() => setBannerVisible(false)}
              className="text-destructive/70 hover:text-destructive transition-colors shrink-0"
              aria-label="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="p-8 flex-1">{children}</div>
      </main>
    </div>
  );
}
