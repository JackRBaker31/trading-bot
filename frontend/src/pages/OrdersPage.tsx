import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Order, PagedResponse } from "@/lib/types";
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
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { formatDate, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Search, X } from "lucide-react";

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Derive a lifecycle status from the order's explicit status field, or fall back to event string. */
function orderLifecycleStatus(order: Order): string {
  if (typeof order.status === "string" && order.status) return order.status.toUpperCase();
  return (order.event ?? "UNKNOWN").toUpperCase();
}

function LifecycleBadge({ status }: { status: string }) {
  const cls =
    status === "APPLIED"
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
      : status === "PENDING" || status === "QUEUED"
        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
        : status === "CANCELLED" || status === "EXPIRED" || status === "FAILED"
          ? "bg-destructive/10 text-destructive border-destructive/20"
          : "bg-muted text-muted-foreground border-border";

  return (
    <span className={cn("px-2 py-0.5 rounded border text-[10px] font-bold uppercase", cls)}>
      {status}
    </span>
  );
}

function SideBadge({ side }: { side: string }) {
  const cls =
    side === "BUY"
      ? "bg-emerald-500/10 text-emerald-400"
      : side === "SELL"
        ? "bg-destructive/10 text-destructive"
        : "bg-muted text-muted-foreground";
  return (
    <span className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase", cls)}>
      {side || "—"}
    </span>
  );
}

// ─── Order Detail Drawer ──────────────────────────────────────────────────────

function OrderDetailDrawer({
  order,
  onClose,
}: {
  order: Order | null;
  onClose: () => void;
}) {
  if (!order) return null;

  const status = orderLifecycleStatus(order);

  // Collect any extra fields from the index signature
  const knownKeys = new Set([
    "timestamp", "reservation_key", "event", "symbol", "side",
    "quantity", "broker_order_id", "reason", "status",
  ]);
  const extraFields = Object.entries(order).filter(
    ([k, v]) => !knownKeys.has(k) && v != null && typeof v !== "object",
  );

  return (
    <Sheet open={!!order} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-3 flex-wrap">
            <SheetTitle className="text-xl font-black font-mono text-primary">
              {order.symbol}
            </SheetTitle>
            <SideBadge side={order.side} />
            <LifecycleBadge status={status} />
          </div>
        </SheetHeader>

        <div className="space-y-6">
          {/* Identity */}
          <DetailSection title="Identity">
            <DetailRow label="Reservation Key" value={order.reservation_key || "—"} mono />
            <DetailRow label="Broker Order ID" value={order.broker_order_id || "—"} mono />
            <DetailRow label="Event Type" value={order.event} />
            <DetailRow label="Status" value={status} />
          </DetailSection>

          {/* Trade details */}
          <DetailSection title="Trade">
            <DetailRow label="Symbol" value={order.symbol} mono />
            <DetailRow label="Side" value={order.side || "—"} />
            <DetailRow
              label="Quantity"
              value={order.quantity != null ? String(order.quantity) : "—"}
              mono
            />
          </DetailSection>

          {/* Timestamps */}
          <DetailSection title="Timestamps">
            <DetailRow label="Created" value={formatDate(order.timestamp)} mono />
          </DetailSection>

          {/* Notes */}
          {order.reason && (
            <DetailSection title="Notes">
              <p className="text-sm text-foreground leading-relaxed">{order.reason}</p>
            </DetailSection>
          )}

          {/* Extra fields from backend */}
          {extraFields.length > 0 && (
            <DetailSection title="Additional Fields">
              {extraFields.map(([k, v]) => (
                <DetailRow key={k} label={k.replace(/_/g, " ")} value={String(v)} mono />
              ))}
            </DetailSection>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function DetailSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
        {title}
      </p>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex justify-between items-start gap-4 text-sm">
      <span className="text-muted-foreground capitalize shrink-0">{label}</span>
      <span className={cn("text-right break-all", mono ? "font-mono text-xs" : "")}>
        {value}
      </span>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function OrdersPage() {
  // ── Filter state ─────────────────────────────────────────────────────────
  const [unresolvedOnly, setUnresolvedOnly] = useState(false);
  const [activeOnly, setActiveOnly] = useState(false);
  const [symbolFilter, setSymbolFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("ALL");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // ── Drawer ───────────────────────────────────────────────────────────────
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  // ── Queries ───────────────────────────────────────────────────────────────
  // Always fetch unresolved count for the persistent banner
  const { data: unresolvedResp } = useQuery({
    queryKey: ["orders-unresolved"],
    queryFn: () => apiClient.get<PagedResponse<Order>>("/orders/unresolved"),
    refetchInterval: 15_000,
  });
  const unresolvedCount = unresolvedResp?.count ?? 0;

  // Main order list
  const endpoint = unresolvedOnly ? "/orders/unresolved" : "/orders";
  const { data: ordersResp, isLoading } = useQuery({
    queryKey: ["orders", unresolvedOnly],
    queryFn: () => apiClient.get<PagedResponse<Order>>(endpoint),
    refetchInterval: 10_000,
  });

  const allOrders = ordersResp?.items ?? [];

  // Derive unique event types from the data
  const eventTypes = useMemo(() => {
    const types = new Set(allOrders.map((o) => o.event).filter(Boolean));
    return Array.from(types).sort();
  }, [allOrders]);

  // ── Client-side filtering ─────────────────────────────────────────────────
  const filtered = useMemo(() => {
    return allOrders.filter((o) => {
      if (symbolFilter && !o.symbol.toLowerCase().includes(symbolFilter.toLowerCase())) return false;
      if (eventTypeFilter !== "ALL" && o.event !== eventTypeFilter) return false;
      if (activeOnly) {
        const s = orderLifecycleStatus(o);
        if (!["PENDING", "QUEUED", "PLACED"].includes(s)) return false;
      }
      if (dateFrom && new Date(o.timestamp) < new Date(dateFrom)) return false;
      if (dateTo && new Date(o.timestamp) > new Date(dateTo + "T23:59:59")) return false;
      return true;
    });
  }, [allOrders, symbolFilter, eventTypeFilter, activeOnly, dateFrom, dateTo]);

  const hasFilters = !!(symbolFilter || eventTypeFilter !== "ALL" || activeOnly || dateFrom || dateTo);

  const resetFilters = () => {
    setSymbolFilter("");
    setEventTypeFilter("ALL");
    setActiveOnly(false);
    setDateFrom("");
    setDateTo("");
  };

  return (
    <div className="space-y-5 max-w-7xl">
      <h2 className="text-sm font-semibold uppercase tracking-wider">
        Order Management
      </h2>

      {/* ── Persistent unresolved banner ──────────────────────────────────── */}
      {unresolvedCount > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-500 text-sm px-4 py-3 rounded-md flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="font-medium">
              {unresolvedCount} unresolved order{unresolvedCount !== 1 ? "s" : ""} require
              attention
            </span>
          </div>
          {!unresolvedOnly && (
            <Button
              variant="outline"
              size="sm"
              className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 hover:text-amber-300 shrink-0"
              onClick={() => setUnresolvedOnly(true)}
            >
              View unresolved
            </Button>
          )}
        </div>
      )}

      {/* ── Filter toolbar ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg border border-border bg-card/50">
        {/* Unresolved toggle */}
        <div className="flex items-center gap-2">
          <Switch
            id="unresolved-mode"
            checked={unresolvedOnly}
            onCheckedChange={setUnresolvedOnly}
          />
          <Label htmlFor="unresolved-mode" className="text-xs uppercase tracking-wider text-muted-foreground cursor-pointer">
            Unresolved Only
          </Label>
        </div>

        <div className="w-px h-5 bg-border" />

        {/* Active only */}
        <div className="flex items-center gap-2">
          <Switch
            id="active-only"
            checked={activeOnly}
            onCheckedChange={setActiveOnly}
          />
          <Label htmlFor="active-only" className="text-xs uppercase tracking-wider text-muted-foreground cursor-pointer">
            Active Only
          </Label>
        </div>

        <div className="w-px h-5 bg-border" />

        {/* Symbol filter */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-muted-foreground" />
          <Input
            placeholder="Symbol…"
            className="h-8 pl-8 text-xs w-32 bg-input/50"
            value={symbolFilter}
            onChange={(e) => setSymbolFilter(e.target.value)}
          />
        </div>

        {/* Event type filter */}
        {eventTypes.length > 0 && (
          <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
            <SelectTrigger className="h-8 text-xs w-40">
              <SelectValue placeholder="Event Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Event Types</SelectItem>
              {eventTypes.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

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

        {/* Reset */}
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="text-muted-foreground h-8">
            <X className="w-3.5 h-3.5 mr-1" />
            Reset
          </Button>
        )}
      </div>

      {/* ── Orders table ───────────────────────────────────────────────────── */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Status</TableHead>
              <TableHead>Symbol</TableHead>
              <TableHead>Side</TableHead>
              <TableHead>Event</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead>Reservation Key</TableHead>
              <TableHead className="text-right">Timestamp</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={7}>
                    <Skeleton className="h-5 w-full" />
                  </TableCell>
                </TableRow>
              ))
            ) : filtered.length > 0 ? (
              filtered.map((order, idx) => (
                <TableRow
                  key={order.reservation_key ?? idx}
                  className="cursor-pointer hover:bg-muted/40"
                  onClick={() => setSelectedOrder(order)}
                >
                  <TableCell>
                    <LifecycleBadge status={orderLifecycleStatus(order)} />
                  </TableCell>
                  <TableCell className="font-bold font-mono text-primary">
                    {order.symbol}
                  </TableCell>
                  <TableCell>
                    <SideBadge side={order.side} />
                  </TableCell>
                  <TableCell className="text-xs uppercase text-muted-foreground">
                    {order.event}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {order.quantity ?? "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {order.reservation_key
                      ? order.reservation_key.substring(0, 12) + "…"
                      : "—"}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-muted-foreground">
                    {formatDate(order.timestamp)}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                  {unresolvedOnly
                    ? "No unresolved orders found."
                    : hasFilters
                      ? "No orders match the current filters."
                      : "No orders found."}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Counts */}
      {!isLoading && filtered.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Showing {filtered.length} of {allOrders.length} orders
          {unresolvedOnly ? " (unresolved)" : ""}
        </p>
      )}

      {/* Detail drawer */}
      <OrderDetailDrawer
        order={selectedOrder}
        onClose={() => setSelectedOrder(null)}
      />
    </div>
  );
}
