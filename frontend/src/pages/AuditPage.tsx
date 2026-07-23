import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { AuditRecord, ListResponse } from "@/lib/types";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { formatDate, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, X, ShieldAlert } from "lucide-react";

// ─── Metadata sanitization ────────────────────────────────────────────────────

/** Keys whose values must always be suppressed (sensitive or stack-trace related). */
const SUPPRESSED_KEY_PATTERNS = [
  "traceback", "stack_trace", "stack", "exception_detail",
  "raw_exception", "error_detail", "debug_info",
];

/** Detect a Python traceback or excessively long error string. */
function looksLikeStackTrace(v: string): boolean {
  return (
    v.includes("Traceback (most recent call last)") ||
    v.includes('File "') ||
    v.length > 1500
  );
}

function sanitizeMetadata(
  meta: Record<string, unknown>,
): Array<{ key: string; value: string; suppressed: boolean }> {
  return Object.entries(meta).map(([k, v]) => {
    const keyLower = k.toLowerCase();
    const isSensitiveKey = SUPPRESSED_KEY_PATTERNS.some((p) => keyLower.includes(p));

    if (isSensitiveKey) {
      return { key: k, value: "[Error details hidden]", suppressed: true };
    }

    const strValue = typeof v === "object" ? JSON.stringify(v, null, 2) : String(v ?? "");

    if (typeof strValue === "string" && looksLikeStackTrace(strValue)) {
      return { key: k, value: "[Error details hidden]", suppressed: true };
    }

    return { key: k, value: strValue, suppressed: false };
  });
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function OutcomeBadge({ outcome }: { outcome: string }) {
  const isSuccess = ["SUCCEEDED", "SUCCESS", "OK", "ALLOWED"].includes(
    outcome.toUpperCase(),
  );
  return (
    <span
      className={cn(
        "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
        isSuccess
          ? "bg-emerald-500/10 text-emerald-400"
          : "bg-destructive/10 text-destructive",
      )}
    >
      {outcome}
    </span>
  );
}

// ─── Audit Detail Drawer ──────────────────────────────────────────────────────

function AuditDetailDrawer({
  record,
  onClose,
}: {
  record: AuditRecord | null;
  onClose: () => void;
}) {
  if (!record) return null;
  const sanitized = sanitizeMetadata(record.metadata ?? {});
  const hasSuppressed = sanitized.some((e) => e.suppressed);

  return (
    <Sheet open={!!record} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-base font-bold uppercase tracking-wide">
            {record.action}
          </SheetTitle>
          <OutcomeBadge outcome={record.outcome} />
        </SheetHeader>

        <div className="space-y-6">
          {/* Core fields */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Event Details
            </p>
            <div className="space-y-1.5">
              {[
                { label: "Event ID",   value: record.event_id },
                { label: "Occurred At", value: formatDate(record.occurred_at) },
                { label: "User",       value: record.username || "System" },
                { label: "Source IP",  value: record.source_ip || "—" },
                { label: "Request ID", value: record.request_id || "—" },
                { label: "Target ID",  value: record.target_id || "—" },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-start gap-4 text-sm">
                  <span className="text-muted-foreground shrink-0">{label}</span>
                  <span className="font-mono text-xs text-right break-all">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Metadata */}
          {sanitized.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Metadata
              </p>
              {hasSuppressed && (
                <div className="flex items-center gap-2 text-xs text-amber-400 mb-2">
                  <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                  Some fields were hidden to protect sensitive information.
                </div>
              )}
              <div className="space-y-1.5">
                {sanitized.map(({ key, value, suppressed }) => (
                  <div key={key} className="flex justify-between items-start gap-4 text-sm">
                    <span className="text-muted-foreground shrink-0 capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span
                      className={cn(
                        "font-mono text-xs text-right break-all",
                        suppressed ? "text-muted-foreground/50 italic" : "",
                      )}
                    >
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AuditPage() {
  // ── Filter state ─────────────────────────────────────────────────────────
  const [usernameFilter, setUsernameFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("ALL");
  const [outcomeFilter, setOutcomeFilter] = useState("ALL");
  const [targetIdFilter, setTargetIdFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // ── Drawer ───────────────────────────────────────────────────────────────
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);

  // ── Query ─────────────────────────────────────────────────────────────────
  const { data: resp, isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: () => apiClient.get<ListResponse<AuditRecord>>("/audit?limit=200"),
  });

  const allRecords = resp?.items ?? [];

  // Derive unique actions and outcomes for dropdowns
  const actions = useMemo(() => {
    return Array.from(new Set(allRecords.map((r) => r.action))).sort();
  }, [allRecords]);

  const outcomes = useMemo(() => {
    return Array.from(new Set(allRecords.map((r) => r.outcome))).sort();
  }, [allRecords]);

  // ── Filtering ─────────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    return allRecords.filter((r) => {
      if (usernameFilter) {
        const uname = (r.username ?? "System").toLowerCase();
        if (!uname.includes(usernameFilter.toLowerCase())) return false;
      }
      if (actionFilter !== "ALL" && r.action !== actionFilter) return false;
      if (outcomeFilter !== "ALL" && r.outcome !== outcomeFilter) return false;
      if (targetIdFilter && !(r.target_id ?? "").toLowerCase().includes(targetIdFilter.toLowerCase())) return false;
      if (dateFrom && new Date(r.occurred_at) < new Date(dateFrom)) return false;
      if (dateTo && new Date(r.occurred_at) > new Date(dateTo + "T23:59:59")) return false;
      return true;
    });
  }, [allRecords, usernameFilter, actionFilter, outcomeFilter, targetIdFilter, dateFrom, dateTo]);

  const hasFilters = !!(
    usernameFilter || actionFilter !== "ALL" || outcomeFilter !== "ALL" || targetIdFilter || dateFrom || dateTo
  );

  const resetFilters = () => {
    setUsernameFilter("");
    setActionFilter("ALL");
    setOutcomeFilter("ALL");
    setTargetIdFilter("");
    setDateFrom("");
    setDateTo("");
  };

  return (
    <div className="space-y-5 max-w-7xl">
      <h2 className="text-sm font-semibold uppercase tracking-wider">Audit Trail</h2>

      {/* ── Filter toolbar ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg border border-border bg-card/50">
        {/* Username */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-muted-foreground" />
          <Input
            placeholder="Username…"
            className="h-8 pl-8 text-xs w-36 bg-input/50"
            value={usernameFilter}
            onChange={(e) => setUsernameFilter(e.target.value)}
          />
        </div>

        {/* Action */}
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="h-8 text-xs w-44">
            <SelectValue placeholder="Action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Actions</SelectItem>
            {actions.map((a) => (
              <SelectItem key={a} value={a}>
                {a}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Outcome */}
        <Select value={outcomeFilter} onValueChange={setOutcomeFilter}>
          <SelectTrigger className="h-8 text-xs w-40">
            <SelectValue placeholder="Outcome" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Outcomes</SelectItem>
            {outcomes.map((o) => (
              <SelectItem key={o} value={o}>
                {o}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Target ID */}
        <div className="relative">
          <Input
            placeholder="Target ID…"
            className="h-8 text-xs w-36 bg-input/50"
            value={targetIdFilter}
            onChange={(e) => setTargetIdFilter(e.target.value)}
          />
        </div>

        <div className="w-px h-5 bg-border" />

        {/* Date range */}
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="h-8 rounded border border-border bg-background text-xs px-2 text-foreground"
            title="From date"
          />
          <span className="text-muted-foreground text-xs">–</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="h-8 rounded border border-border bg-background text-xs px-2 text-foreground"
            title="To date"
          />
        </div>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="text-muted-foreground h-8">
            <X className="w-3.5 h-3.5 mr-1" />
            Reset
          </Button>
        )}
      </div>

      {/* ── Audit table ────────────────────────────────────────────────────── */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[160px]">Timestamp</TableHead>
              <TableHead className="w-[100px]">User</TableHead>
              <TableHead>Action</TableHead>
              <TableHead className="w-[110px]">Outcome</TableHead>
              <TableHead className="w-[140px]">Target ID</TableHead>
              <TableHead className="w-[100px]">Source IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={6}>
                    <Skeleton className="h-5 w-full" />
                  </TableCell>
                </TableRow>
              ))
            ) : filtered.length > 0 ? (
              filtered.map((rec) => (
                <TableRow
                  key={rec.event_id}
                  className="cursor-pointer hover:bg-muted/40"
                  onClick={() => setSelectedRecord(rec)}
                >
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {formatDate(rec.occurred_at)}
                  </TableCell>
                  <TableCell className="text-xs font-medium">
                    {rec.username || "System"}
                  </TableCell>
                  <TableCell className="text-xs">{rec.action}</TableCell>
                  <TableCell>
                    <OutcomeBadge outcome={rec.outcome} />
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {rec.target_id || "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground opacity-50">
                    {rec.source_ip || "—"}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                  {hasFilters ? "No audit records match the current filters." : "No audit records found."}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Counts */}
      {!isLoading && (
        <p className="text-xs text-muted-foreground">
          Showing {filtered.length} of {allRecords.length} records
        </p>
      )}

      {/* Detail drawer */}
      <AuditDetailDrawer
        record={selectedRecord}
        onClose={() => setSelectedRecord(null)}
      />
    </div>
  );
}
