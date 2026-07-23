import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Portfolio, Position, ListResponse } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatGBP } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { usePositionPrices } from "@/hooks/usePositionPrices";

export default function PortfolioPage() {
  const { data: portfolio, isLoading: loadingPortfolio } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => apiClient.get<Portfolio>("/portfolio"),
    refetchInterval: 10000,
  });

  const { data: positionsResp, isLoading: loadingPositions } = useQuery({
    queryKey: ["positions"],
    queryFn: () => apiClient.get<ListResponse<Position>>("/positions"),
    refetchInterval: 10000,
  });

  const positions = positionsResp?.items ?? [];
  const positionSymbols = positions.map((p) => p.symbol);

  const { data: priceMap = {} } = usePositionPrices(positionSymbols, 10000);

  const hasPrices = positionSymbols.some((s) => priceMap[s] !== undefined);
  const allPriced = positionSymbols.length > 0 && positionSymbols.every((s) => priceMap[s] !== undefined);

  const positionMarketValue = positions.reduce((sum, p) => {
    const price = priceMap[p.symbol];
    return price !== undefined ? sum + p.quantity * price : sum;
  }, 0);

  const cash = portfolio?.cash ?? null;
  const totalValue = cash !== null ? cash + positionMarketValue : null;

  return (
    <div className="space-y-6 max-w-7xl">
      <h2 className="text-sm font-semibold uppercase tracking-wider mb-2">
        Portfolio Overview
      </h2>

      {portfolio && !portfolio.available && (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-500 text-sm px-4 py-3 rounded-md flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>Portfolio data is not yet available — run a trading cycle first.</span>
        </div>
      )}

      {positions.length > 0 && !hasPrices && (
        <div className="bg-muted text-muted-foreground text-sm px-4 py-3 rounded-md border flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-foreground">Live valuations unavailable</p>
            <p className="text-xs mt-1">
              No price data found for open positions. Run a news research cycle to populate prices.
            </p>
          </div>
        </div>
      )}

      {positions.length > 0 && hasPrices && !allPriced && (
        <div className="bg-muted text-muted-foreground text-sm px-4 py-3 rounded-md border flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-foreground">Partial valuations</p>
            <p className="text-xs mt-1">
              Price data is missing for some positions — total value may be understated.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs uppercase text-muted-foreground tracking-wider mb-1">
              Portfolio Value
            </div>
            <div className="text-xl font-mono text-foreground">
              {loadingPortfolio ? (
                <Skeleton className="h-7 w-24" />
              ) : totalValue !== null ? (
                <>
                  {formatGBP(totalValue)}
                  <span className="text-xs text-muted-foreground ml-1 font-sans">
                    {positions.length === 0
                      ? "cash"
                      : allPriced
                      ? "total"
                      : hasPrices
                      ? "partial"
                      : "cash only"}
                  </span>
                </>
              ) : (
                "—"
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs uppercase text-muted-foreground tracking-wider mb-1">
              Current Cash
            </div>
            <div className="text-xl font-mono text-accent">
              {loadingPortfolio ? (
                <Skeleton className="h-7 w-24" />
              ) : (
                formatGBP(portfolio?.cash)
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs uppercase text-muted-foreground tracking-wider mb-1">
              Positions Value
            </div>
            <div className="text-xl font-mono text-foreground">
              {loadingPortfolio || loadingPositions ? (
                <Skeleton className="h-7 w-24" />
              ) : hasPrices ? (
                formatGBP(positionMarketValue)
              ) : (
                "—"
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-xs uppercase text-muted-foreground tracking-wider mb-1">
              Starting Cash
            </div>
            <div className="text-xl font-mono text-foreground">
              {loadingPortfolio ? (
                <Skeleton className="h-7 w-24" />
              ) : (
                formatGBP(portfolio?.starting_cash)
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-8">
        <div className="p-4 border-b">
          <h3 className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
            Open Positions
          </h3>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Symbol</TableHead>
              <TableHead className="text-right">Quantity</TableHead>
              <TableHead className="text-right">Last Price</TableHead>
              <TableHead className="text-right">Market Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loadingPositions ? (
              Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={4}>
                    <Skeleton className="h-6 w-full" />
                  </TableCell>
                </TableRow>
              ))
            ) : positions.length > 0 ? (
              positions.map((pos) => {
                const price = priceMap[pos.symbol];
                const marketValue =
                  price !== undefined ? pos.quantity * price : undefined;
                return (
                  <TableRow key={pos.symbol}>
                    <TableCell className="font-bold">{pos.symbol}</TableCell>
                    <TableCell className="text-right font-mono">
                      {pos.quantity}
                    </TableCell>
                    <TableCell className="text-right font-mono text-muted-foreground">
                      {price !== undefined ? formatGBP(price) : "—"}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {marketValue !== undefined ? formatGBP(marketValue) : "—"}
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="h-32 text-center text-muted-foreground"
                >
                  No open positions.
                </TableCell>
              </TableRow>
            )}
            {positions.length > 0 && (cash !== null || hasPrices) && (
              <TableRow className="border-t-2 font-semibold bg-muted/30 hover:bg-muted/30">
                <TableCell colSpan={3} className="text-right text-muted-foreground">
                  Total Portfolio Value
                </TableCell>
                <TableCell className="text-right font-mono font-bold">
                  {totalValue !== null ? formatGBP(totalValue) : "—"}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
