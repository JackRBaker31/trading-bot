import { useState } from "react";
import { BrainCircuit, FlaskConical, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { useResearchLabBrief } from "@/hooks/useResearchLabBrief";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

export default function ResearchLabPage() {
  const [days, setDays] = useState<1 | 7 | 30>(7);
  const { data, isLoading, error } = useResearchLabBrief(days);
  if (isLoading) return <div className="p-8 text-muted-foreground">Building deterministic research brief…</div>;
  if (error || !data) return <div className="p-8 text-red-400">Research Lab brief is unavailable.</div>;
  const e = data.evidence;
  return <div className="max-w-[1550px] space-y-5 p-8">
    <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
      <div className="flex gap-3"><div className="rounded-xl border border-primary/20 bg-primary/10 p-3 text-primary"><BrainCircuit className="h-6 w-6" /></div><div><div className="flex items-center gap-2"><h1 className="text-2xl font-semibold">AI Research Lab</h1><Badge variant="outline">Epoch 1 · Package 1.1</Badge><Badge variant="outline">Research only</Badge></div><p className="mt-2 max-w-4xl text-sm text-muted-foreground">Evidence-backed self-analysis. Findings and experiments are deterministic and never alter trading automatically.</p></div></div>
      <div className="flex gap-2">{([1,7,30] as const).map(value => <Button key={value} variant={days===value?"default":"outline"} onClick={()=>setDays(value)}>{value===1?"24 Hours":`${value} Days`}</Button>)}</div>
    </section>
    <Card className="border-primary/20"><CardContent className="p-6"><div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Morning research brief</p><h2 className="mt-2 text-xl font-semibold">{data.headline}</h2><p className="mt-2 max-w-5xl text-sm leading-6 text-muted-foreground">{data.summary}</p></div><Badge variant="outline">{data.status.replaceAll("_"," ")}</Badge></div></CardContent></Card>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {[['Shadow decisions',e.shadow_decisions],['Measured 1D',e.measured_1d_decisions],['Directional',`${e.directional_success_percent}%`],['After cost',`${e.profitable_after_cost_percent}%`],['Calibration sample',e.calibration_sample_size],['Healthy jobs',`${e.healthy_completion_percent}%`]].map(([label,value])=><Card key={String(label)}><CardContent className="p-4"><p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{label}</p><p className="mt-2 font-mono text-2xl font-black">{value}</p></CardContent></Card>)}
    </div>
    <div className="grid gap-4 xl:grid-cols-[1.25fr_1fr]">
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4 text-primary"/>Evidence-backed findings</CardTitle></CardHeader><CardContent className="space-y-3">{data.findings.map((f,i)=><div key={`${f.kind}-${i}`} className="rounded-lg border p-4"><div className="flex items-center justify-between gap-3"><strong>{f.title}</strong><Badge variant="outline">{f.confidence}</Badge></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{f.statement}</p><p className="mt-2 text-xs text-muted-foreground">Sample: {f.sample_size}</p></div>)}</CardContent></Card>
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FlaskConical className="h-4 w-4 text-primary"/>Suggested experiments</CardTitle></CardHeader><CardContent className="space-y-3">{data.suggested_experiments.map(x=><div key={x.experiment_id} className="rounded-lg border p-4"><div className="flex items-center justify-between"><strong>{x.title}</strong><Badge variant="outline">{x.status}</Badge></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{x.hypothesis}</p><div className="mt-3"><div className="mb-1 flex justify-between text-xs"><span>Evidence progress</span><span>{x.current_sample}/{x.required_sample}</span></div><Progress value={Math.min(100,x.current_sample/Math.max(1,x.required_sample)*100)}/></div><p className="mt-2 text-xs text-muted-foreground">Risk: {x.risk} · Automatic change: No</p></div>)}</CardContent></Card>
    </div>
    <div className="grid gap-4 xl:grid-cols-2">
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><TrendingUp className="h-4 w-4 text-primary"/>Sector evidence</CardTitle></CardHeader><CardContent className="space-y-3">{data.sector_leaders.map(s=><div key={s.sector} className="grid grid-cols-[1fr_auto_auto] gap-4 rounded-md border p-3 text-sm"><strong>{s.sector}</strong><span>{s.measured_count} measured</span><span>{s.directional_accuracy_percent}% accuracy</span></div>)}</CardContent></Card>
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-4 w-4 text-primary"/>Methodology & safety</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><p>Deterministic analysis: <strong>Yes</strong></p><p>External language model: <strong>No</strong></p><p>Automatic model changes: <strong>No</strong></p><p>Trading impact: <strong>{data.trading_impact}</strong></p><p>First serious review sample: <strong>{data.methodology.minimum_serious_review_sample}</strong></p><p className="text-muted-foreground">{data.methodology.source}</p></CardContent></Card>
    </div>
  </div>;
}
