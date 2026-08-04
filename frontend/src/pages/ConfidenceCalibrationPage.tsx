import { useState } from "react";
import { Activity, Gauge, ShieldCheck, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useConfidenceCalibration } from "@/hooks/useConfidenceCalibration";

const fmt = (value: number) => `${value.toFixed(1)}%`;

export default function ConfidenceCalibrationPage() {
  const [days, setDays] = useState<1 | 7 | 30>(7);
  const { data, isLoading, error } = useConfidenceCalibration(days);

  if (isLoading) return <div className="p-8 text-sm text-muted-foreground">Loading confidence calibration…</div>;
  if (error || !data) return <div className="p-8 text-sm text-destructive">Confidence calibration is unavailable.</div>;

  return (
    <div className="space-y-5 max-w-7xl">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Gauge className="h-7 w-7 text-[#D4AF37]" />
            <div>
              <h1 className="text-2xl font-semibold">Confidence Calibration</h1>
              <p className="text-sm text-muted-foreground">Compare stored confidence with realised one-day directional accuracy.</p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {([1, 7, 30] as const).map((value) => (
            <Button key={value} variant={days === value ? "default" : "outline"} onClick={() => setDays(value)}>
              {value === 1 ? "24 Hours" : `${value} Days`}
            </Button>
          ))}
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="Measured outcomes" value={String(data.summary.sample_size)} detail={`First serious review at ${data.methodology.minimum_review_sample}`} />
        <Metric title="Calibration error" value={`${data.summary.mean_absolute_error_points.toFixed(1)} pts`} detail="Mean absolute expected-vs-observed gap" />
        <Metric title="Drift" value={`${data.summary.drift_points >= 0 ? "+" : ""}${data.summary.drift_points.toFixed(1)} pts`} detail={data.summary.drift_status} />
        <Metric title="Status" value={data.status.replaceAll("_", " ")} detail="Trading impact: NONE" />
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm uppercase tracking-wider">Reliability by confidence band</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-muted-foreground"><tr><th className="p-2 text-left">Band</th><th className="p-2 text-center">Sample</th><th className="p-2 text-center">Expected</th><th className="p-2 text-center">Observed</th><th className="p-2 text-center">Gap</th><th className="p-2 text-left">Assessment</th></tr></thead>
              <tbody>{data.buckets.map((bucket) => <tr key={bucket.name} className="border-t"><td className="p-2 font-medium">{bucket.label}</td><td className="p-2 text-center font-mono">{bucket.measured_count}</td><td className="p-2 text-center font-mono">{fmt(bucket.expected_accuracy_percent)}</td><td className="p-2 text-center font-mono">{fmt(bucket.observed_accuracy_percent)}</td><td className="p-2 text-center font-mono">{bucket.calibration_gap_points > 0 ? "+" : ""}{bucket.calibration_gap_points.toFixed(1)} pts</td><td className="p-2"><Badge variant="outline">{bucket.assessment.replaceAll("_", " ")}</Badge></td></tr>)}</tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card><CardHeader><CardTitle className="text-sm uppercase tracking-wider flex items-center gap-2"><TrendingUp className="h-4 w-4" />Calibration findings</CardTitle></CardHeader><CardContent className="space-y-3"><p className="text-sm">Best aligned band: <strong>{data.summary.best_band ?? "Not available"}</strong></p><p className="text-sm">Weakest aligned band: <strong>{data.summary.weakest_band ?? "Not available"}</strong></p><p className="text-xs text-muted-foreground">Expected accuracy is the average stored confidence. Observed accuracy is measured one-day directional success.</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm uppercase tracking-wider flex items-center gap-2"><ShieldCheck className="h-4 w-4" />Research recommendations</CardTitle></CardHeader><CardContent className="space-y-3">{data.recommendations.length ? data.recommendations.map((item) => <div key={`${item.code}-${item.title}`} className="rounded-lg border p-3"><p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs text-muted-foreground">{item.reason}</p><p className="mt-2 text-[10px] uppercase tracking-wider text-[#D4AF37]">Automatic change: No</p></div>) : <p className="text-sm text-muted-foreground">No calibration experiment is currently recommended.</p>}</CardContent></Card>
      </div>

      <Card><CardContent className="p-4 flex items-start gap-3"><Activity className="h-5 w-5 text-[#D4AF37]" /><div><p className="text-sm font-semibold">Safety boundary</p><p className="text-xs text-muted-foreground">This package is read-only. It does not alter confidence scores, ranking weights, graduation rules, risk controls or execution.</p></div></CardContent></Card>
    </div>
  );
}

function Metric({ title, value, detail }: { title: string; value: string; detail: string }) {
  return <Card><CardContent className="p-4"><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground">{title}</p><p className="mt-2 font-mono text-2xl font-black">{value}</p><p className="mt-1 text-xs text-muted-foreground">{detail}</p></CardContent></Card>;
}
