import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const s = status?.toUpperCase() || "UNKNOWN";

  let colors = "bg-muted text-muted-foreground border-muted-border";
  let dot = false;
  let dotColor = "";

  if (s === "RUNNING" || s === "STARTING" || s === "BUSY") {
    colors = "bg-accent/10 text-accent border-accent/20";
    dot = true;
    dotColor = "bg-accent animate-pulse";
  } else if (s === "SUCCEEDED" || s === "PROMISING") {
    colors = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  } else if (s === "SUCCEEDED_WITH_WARNINGS" || s === "STOP_REQUESTED") {
    colors = "bg-amber-500/10 text-amber-400 border-amber-500/20";
  } else if (s === "FAILED" || s === "REJECTED" || s === "STOPPED") {
    colors =
      "bg-destructive/10 text-destructive-foreground border-destructive/20";
  } else if (s === "QUEUED") {
    colors = "bg-blue-500/10 text-blue-400 border-blue-500/20";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border",
        colors,
        className,
      )}
    >
      {dot && <span className={cn("w-1.5 h-1.5 rounded-full", dotColor)} />}
      {s.replace(/_/g, " ")}
    </span>
  );
}
