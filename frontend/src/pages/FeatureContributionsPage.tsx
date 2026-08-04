import { useState } from "react";
import { Activity, BarChart3, BrainCircuit, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useFeatureContributions } from "@/hooks/useFeatureContributions";

const pct = (value: number | null) => value == null ? "—" : `${value.toFixed(2)}%`;
const num = (value: number | null) => value == null ? "—" : value.toFixed(2);

export default function FeatureContributionsPage() {
  const [days, setDays] = useState<7 | 30 | 90 | 365>(90);
  const [horizon, setHorizon] = useState<1 | 5 | 20>(1);
  const { data, isLoading, error } = useFeatureContributions(days, horizon);

  if (isLoading) return <div className="p-8 text-sm text-muted-foreground">Loading feature evidence…</div>;
  if (error || !data) return <div className="p-8 text-sm text-destructive">Feature contribution evidence is unavailable.</div>;

  return (
    <div className="space-y-5 p-8 max-w-[1550px]">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-[#D4AF37]/30 bg-[#D4AF37]/10 p-3"><BrainCircuit className="h-6 w-6 text-[#D4AF37]" /></div>
          <div>
            <div className="flex flex-wrap items-center gap-2"><h1 className="text-2xl font-semibold">Feature Contribution Engine</h1><Badge variant="outline">Epoch 1.3</Badge><Badge variant="outline">Research only</Badge></div>
            <p className="mt-2 max-w-4xl text-sm text-muted-foreground">Measures how persisted opportunity-score components relate to realised forward returns. No weights are changed automatically.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {[7,30,90,365].map((value) => <Button key={value} variant={days === value ? "default" : "outline"} size="sm" onClick={() => setDays(value as 7|30|90|365)}>{value}D</Button>)}
          {[1,5,20].map((value) => <Button key={value} variant={horizon === value ? "default" : "outline"} size="sm" onClick={() => setHorizon(value as 1|5|20)}>{value}D outcome</Button>)}
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="Tracked snapshots" value={String(data.summary.tracked_snapshot_count)} detail={`${days}-day evidence window`} />
        <Metric title="Measured outcomes" value={String(data.summary.measured_outcome_count)} detail={`${horizon}-day realised results`} />
        <Metric title="Features" value={String(data.summary.feature_count)} detail="Persisted score components" />
        <Metric title="Positive alpha" value={String(data.summary.positive_feature_count)} detail="Features with positive average alpha" />
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm uppercase tracking-wider flex items-center gap-2"><BarChart3 className="h-4 w-4" />Feature performance</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-muted-foreground"><th className="p-2">Feature</th><th className="p-2 text-center">Sample</th><th className="p-2 text-center">Avg contribution</th><th className="p-2 text-center">Hit rate</th><th className="p-2 text-center">Avg return</th><th className="p-2 text-center">Avg alpha</th><th className="p-2 text-center">Correlation</th><th className="p-2">Evidence</th></tr></thead>
              <tbody>{data.features.map((item) => <tr key={item.code} className="border-t"><td className="p-2 font-medium">{item.label}</td><td className="p-2 text-center font-mono">{item.measured_count}</td><td className="p-2 text-center font-mono">{num(item.average_contribution)}</td><td className="p-2 text-center font-mono">{pct(item.directional_success_percent)}</td><td className="p-2 text-center font-mono">{pct(item.average_return_percent)}</td><td className="p-2 text-center font-mono">{pct(item.average_alpha_percent)}</td><td className="p-2 text-center font-mono">{num(item.contribution_return_correlation)}</td><td className="p-2"><Badge variant="outline">{item.evidence}</Badge></td></tr>)}</tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card><CardHeader><CardTitle className="text-sm uppercase tracking-wider">Latest feature vectors</CardTitle></CardHeader><CardContent className="space-y-3">{data.latest_vectors.slice(0,6).map((vector) => <div key={vector.snapshot_id} className="rounded-lg border p-3"><div className="flex items-center justify-between"><div><span className="font-semibold">{vector.symbol}</span><span className="ml-2 text-xs text-muted-foreground">Rank {vector.rank}</span></div><span className="font-mono text-sm">{vector.opportunity_score.toFixed(1)}</span></div><div className="mt-2 flex flex-wrap gap-2">{vector.components.slice(0,5).map((component) => <Badge key={component.code} variant="outline">{component.label}: {component.value.toFixed(1)}</Badge>)}</div></div>)}</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm uppercase tracking-wider flex items-center gap-2"><Activity className="h-4 w-4" />Research recommendations</CardTitle></CardHeader><CardContent className="space-y-3">{data.recommendations.length ? data.recommendations.map((item) => <div key={item.code} className="rounded-lg border p-3"><p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs text-muted-foreground">{item.reason}</p><p className="mt-2 text-[10px] uppercase tracking-wider text-[#D4AF37]">Automatic change: No</p></div>) : <p className="text-sm text-muted-foreground">No feature review is currently recommended.</p>}</CardContent></Card>
      </div>

      <Card><CardContent className="p-4 flex items-start gap-3"><ShieldCheck className="h-5 w-5 text-[#D4AF37]" /><div><p className="text-sm font-semibold">Safety boundary</p><p className="text-xs text-muted-foreground">Read-only analytics. Ranking weights, confidence, graduation, risk and execution remain unchanged.</p></div></CardContent></Card>
    </div>
  );
}

function Metric({ title, value, detail }: { title: string; value: string; detail: string }) {
  return <Card><CardContent className="p-4"><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">{title}</p><p className="mt-2 font-mono text-2xl font-black">{value}</p><p className="mt-1 text-xs text-muted-foreground">{detail}</p></CardContent></Card>;
}
