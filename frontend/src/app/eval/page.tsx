"use client";
import { useEffect, useState } from "react";
import { j, post } from "../api";
export default function Eval() {
  const [t, setT] = useState<any>(null); const [r, setR] = useState<any>(null); const [busy, setBusy] = useState(false);
  useEffect(() => { j("/api/eval/telemetry").then(setT); }, []);
  const run = async () => { setBusy(true); setR(await post("/api/eval/run", {})); j("/api/eval/telemetry").then(setT); setBusy(false); };
  return (<div className="space-y-4"><h1 className="text-2xl font-semibold">Evaluation and telemetry</h1>
    {t && <div className="card text-sm">LLM calls: {t.calls} · Avg latency: {t.avg_latency_ms} ms · Spend: ₹{t.total_cost_inr}</div>}
    <button className="btn btn-primary" onClick={run} disabled={busy}>{busy ? "Running…" : "Run benchmark"}</button>
    {r && <pre className="card text-xs overflow-auto">{JSON.stringify(r, null, 2)}</pre>}</div>);
}
