import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Database,
  History,
  Layers3,
  Network,
  RefreshCw,
  Server,
  ShieldCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  UniverseCycleCoverage,
  UniverseVersion,
  useUniverseGovernance,
} from "@/hooks/useUniverseGovernance";
import { cn } from "@/lib/utils";

function displayName(value: string): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function MetricCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: typeof Network;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
            {label}
          </p>
          <p className="mt-2 font-mono text-2xl font-black">{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
        </div>
        <div className="rounded-lg border border-primary/20 bg-primary/10 p-2 text-primary">
          <Icon className="h-4 w-4" />
        </div>
      </CardContent>
    </Card>
  );
}

function CoverageRow({ item }: { item: UniverseCycleCoverage }) {
  const healthy = item.coverage_percent >= 99.9 && item.skipped_count === 0;
  return (
    <div className="grid gap-3 rounded-lg border p-3 text-sm md:grid-cols-[190px_1fr_120px_120px] md:items-center">
      <div>
        <p className="font-medium">{new Date(item.captured_at).toLocaleString()}</p>
        <p className="text-[10px] text-muted-foreground">{item.source}</p>
      </div>
      <div>
        <div className="flex items-center justify-between text-xs">
          <span>{item.processed_count} / {item.requested_count} processed</span>
          <span className={healthy ? "text-emerald-400" : "text-amber-400"}>
            {item.coverage_percent.toFixed(1)}%
          </span>
        </div>
        <Progress value={item.coverage_percent} className="mt-2 h-2" />
      </div>
      <div className="font-mono text-xs text-muted-foreground">
        {item.version_id}
      </div>
      <div className={cn("text-right text-xs font-bold", healthy ? "text-emerald-400" : "text-amber-400")}>
        {healthy ? "COMPLETE" : `${item.skipped_count} SKIPPED`}
      </div>
    </div>
  );
}

function VersionRow({ version }: { version: UniverseVersion }) {
  return (
    <div className="rounded-lg border p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-mono text-sm font-bold text-primary">{version.version_id}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {new Date(version.created_at).toLocaleString()} · {version.symbol_count} symbols
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px] font-bold uppercase tracking-wider">
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-emerald-400">
            +{version.added_symbols.length} added
          </span>
          <span className="rounded-full border border-destructive/30 bg-destructive/10 px-2 py-1 text-destructive">
            -{version.removed_symbols.length} removed
          </span>
        </div>
      </div>
      {(version.added_symbols.length > 0 || version.removed_symbols.length > 0) && (
        <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
          <p className="text-emerald-400">
            Added: {version.added_symbols.slice(0, 20).join(", ") || "None"}
          </p>
          <p className="text-destructive">
            Removed: {version.removed_symbols.slice(0, 20).join(", ") || "None"}
          </p>
        </div>
      )}
    </div>
  );
}

export default function UniverseGovernancePage() {
  const { data, isLoading, isError, error, refetch, isFetching } =
    useUniverseGovernance();

  if (isLoading) {
    return (
      <div className="space-y-5 p-8">
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-[520px]" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-8">
        <Card className="border-destructive/30">
          <CardContent className="flex items-start gap-3 p-5">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-destructive" />
            <div>
              <p className="font-semibold">Universe Governance is unavailable</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error ? error.message : "The universe report could not be loaded."}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const latestCoverage = data.latest_cycle_coverage;
  const valid = data.eligibility_status === "VALID";

  return (
    <div className="max-w-[1550px] space-y-5 p-8">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary">
            <Network className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Universe Governance</h1>
              <span className="rounded-full border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#D4AF37]">
                v0.12
              </span>
              <span className={cn(
                "rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]",
                valid
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-400",
              )}>
                {displayName(data.eligibility_status)}
              </span>
            </div>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-muted-foreground">
              Versions the active stock universe, validates eligibility, measures cycle coverage and preserves rank comparability as the universe expands.
            </p>
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">{data.source_path}</p>
          </div>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={cn("mr-2 h-4 w-4", isFetching && "animate-spin")} />
          Refresh governance
        </Button>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Active universe"
          value={String(data.current_version.symbol_count)}
          hint={data.current_version.version_id}
          icon={Layers3}
        />
        <MetricCard
          label="Cache coverage"
          value={`${data.cache_coverage_percent.toFixed(1)}%`}
          hint={`${data.cached_symbol_count} cached · ${data.uncached_symbol_count} uncached`}
          icon={Database}
        />
        <MetricCard
          label="Latest cycle coverage"
          value={latestCoverage ? `${latestCoverage.coverage_percent.toFixed(1)}%` : "—"}
          hint={latestCoverage ? `${latestCoverage.processed_count}/${latestCoverage.requested_count} processed` : "No governed cycle recorded yet"}
          icon={Activity}
        />
        <MetricCard
          label="Estimated request load"
          value={String(data.estimated_live_requests)}
          hint={`${data.estimated_budget_percent.toFixed(1)}% of ${data.daily_request_budget}/day budget`}
          icon={Server}
        />
      </div>

      {(data.rank_comparability_warning || data.warnings.length > 0) && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
            <div className="space-y-1 text-sm">
              {data.rank_comparability_warning && (
                <p className="font-semibold text-amber-300">{data.rank_comparability_warning}</p>
              )}
              {data.warnings.map((warning) => <p key={warning}>{warning}</p>)}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Layers3 className="h-4 w-4 text-primary" />
              Sector and universe distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.group_summaries.map((group) => (
              <div key={group.name} className="rounded-lg border p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">{group.name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {group.symbols.join(", ")}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-lg font-bold">{group.symbol_count}</p>
                    <p className="text-[10px] text-muted-foreground">{group.share_percent.toFixed(1)}%</p>
                  </div>
                </div>
                <Progress value={group.share_percent} className="mt-3 h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <ShieldCheck className="h-4 w-4 text-primary" />
              Eligibility and expansion readiness
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3 rounded-lg border p-4">
              {valid ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-400" />
              ) : (
                <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-400" />
              )}
              <div>
                <p className="font-semibold">{displayName(data.eligibility_status)}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {data.invalid_symbols.length} invalid · {data.duplicate_symbols.length} duplicate
                </p>
              </div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="flex items-center justify-between text-sm">
                <span>Historical cache warm-up</span>
                <span className="font-mono font-bold">{data.cache_coverage_percent.toFixed(1)}%</span>
              </div>
              <Progress value={data.cache_coverage_percent} className="mt-3 h-2" />
              <p className="mt-2 text-xs text-muted-foreground">
                Uncached first-pass estimate: {data.estimated_live_requests} live requests.
              </p>
            </div>
            <div className="rounded-lg border p-4 text-xs text-muted-foreground">
              <p className="font-semibold text-foreground">Current version checksum</p>
              <p className="mt-2 break-all font-mono">{data.current_version.checksum}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Activity className="h-4 w-4 text-primary" />
            Intelligence Cycle universe coverage
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.recent_cycle_coverage.length > 0 ? (
            data.recent_cycle_coverage.slice(0, 12).map((item) => (
              <CoverageRow key={item.coverage_id} item={item} />
            ))
          ) : (
            <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">
              The next Intelligence Cycle will create the first governed coverage record.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <History className="h-4 w-4 text-primary" />
            Universe version history
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.versions.map((version) => (
            <VersionRow key={version.version_id} version={version} />
          ))}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>{data.governance_version}</span>
        <span>Generated {new Date(data.generated_at).toLocaleString()}</span>
      </div>
    </div>
  );
}
