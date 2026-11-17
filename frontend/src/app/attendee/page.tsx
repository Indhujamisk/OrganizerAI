"use client";
import { useEffect, useState } from "react";
import { j, post } from "../api";
export default function Attendee() {
  const [ev, setEv] = useState<any>(null); const [q, setQ] = useState(""); const [log, setLog] = useState<any[]>([]); const [esc, setEsc] = useState<string[]>([]);
  useEffect(() => { j("/api/events").then(e => e.length && setEv(e[0])); }, []);
  const ask = async () => { const r = await post("/api/rag/ask", { event_id: ev.id, question: q }); setLog([...log, { q, r }]); setQ(""); };
  if (!ev) return <p>No event yet.</p>;
  return (<div className="grid md:grid-cols-2 gap-6">
    <div className="card"><h1 className="text-2xl font-semibold">{ev.name}</h1><p className="text-sm mb-3">{ev.city} · {ev.date}</p>
      {(ev.plan?.agenda || []).map((a: any, i: number) => <div key={i} className="text-sm border-t border-line py-1">{a.start}–{a.end} · {a.title} <span className="text-xs">({a.speaker})</span></div>)}
      <button className="btn btn-primary mt-4">Register</button></div>
    <div className="card flex flex-col gap-3"><h2 className="font-medium">Ask about the event</h2>
      {log.map((m, i) => <div key={i} className="text-sm"><p className="font-medium">{m.q}</p><p>{m.r.answer}</p>
        <p className="text-xs">Confidence {m.r.confidence}{m.r.citations.map((c: any) => ` · ${c.source} p.${c.page}`)}</p>
        {m.r.escalate && (esc.includes(m.q) ? <p className="text-xs text-green-700">Sent to organizer.</p> : <button className="btn mt-1" onClick={() => setEsc([...esc, m.q])}>Escalate to organizer</button>)}</div>)}
      <div className="flex gap-2"><input className="flex-1 border border-line rounded px-2" value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === "Enter" && ask()} placeholder="e.g. What time do doors open?" />
        <button className="btn btn-primary" onClick={ask}>Ask</button></div></div></div>);
}
