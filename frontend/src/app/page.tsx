"use client";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { j, inr } from "./api";

export default function Dashboard() {
  const [events, setEvents] = useState<any[]>([]); const [ev, setEv] = useState<any>(null); const [risk, setRisk] = useState<any>(null);
  useEffect(() => { j("/api/events").then(setEvents); }, []);
  const load = (id: number) => { j(`/api/events/${id}`).then(setEv); j(`/api/analytics/${id}`).then(setRisk); };
  useEffect(() => { if (events.length && !ev) load(events[events.length - 1].id); }, [events]);
  if (!ev) return <p>Loading… If empty, run <code>python seed_demo.py</code> in backend.</p>;
  const budget = ev.plan?.budget || []; const agenda = ev.plan?.agenda || [];
  const conflicts: string[] = [];
  agenda.forEach((a: any, i: number) => agenda.slice(i + 1).forEach((b: any) => { if (a.speaker === b.speaker && a.start < b.end && b.start < a.end) conflicts.push(`${a.speaker} is double-booked: "${a.title}" and "${b.title}"`); }));
  return (<div className="space-y-6">
    <div className="flex items-end justify-between flex-wrap gap-2">
      <div><h1 className="text-2xl font-semibold">{ev.name}</h1><p className="text-sm">{ev.city} · {ev.date} · {ev.headcount} guests · {inr(ev.budget_inr)}</p></div>
      <select className="border border-line rounded px-2 py-1 bg-white" value={ev.id} onChange={e => load(+e.target.value)}>{events.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}</select>
    </div>
    <section className="grid md:grid-cols-3 gap-4">
      <div className="card"><h2 className="font-medium mb-2">Task board</h2>
        {ev.tasks.map((t: any) => <div key={t.id} className="border-b border-line py-2 text-sm"><b>{t.title}</b>
          {t.depends_on?.length > 0 && <div className="text-xs">Needs: {t.depends_on.join(", ")}</div>}
          {t.ai_flag && <div className="text-xs text-amber-700">{t.ai_flag}</div>}</div>)}</div>
      <div className="card md:col-span-2"><h2 className="font-medium mb-2">Budget with GST</h2>
        <div className="h-48"><ResponsiveContainer><BarChart data={budget}><XAxis dataKey="category" fontSize={10} /><YAxis fontSize={10} tickFormatter={v => v / 1000 + "k"} /><Tooltip formatter={(v: any) => inr(v)} />
          <Bar dataKey="base_inr" stackId="a" fill="#12302E" name="Base" /><Bar dataKey="gst_inr" stackId="a" fill="#E8A317" name="GST" /></BarChart></ResponsiveContainer></div>
        <table className="w-full text-sm mt-2"><thead><tr className="text-left"><th>Category</th><th>Base</th><th>GST</th><th>Total</th></tr></thead>
          <tbody>{budget.map((b: any) => <tr key={b.category} className="border-t border-line"><td>{b.category}</td><td>{inr(b.base_inr)}</td><td>{inr(b.gst_inr)} ({b.gst_rate * 100}%)</td><td>{inr(b.total_inr)}</td></tr>)}</tbody></table></div>
    </section>
    <section className="grid md:grid-cols-3 gap-4">
      <div className="card"><h2 className="font-medium mb-2">Risk forecast</h2>
        <p className="text-sm">No-show probability</p><p className="text-3xl font-semibold">{risk ? Math.round(risk.noshow_prob * 100) : "–"}%</p>
        <p className="text-sm mt-2">Budget overrun risk</p><p className="text-3xl font-semibold">{risk ? Math.round(risk.overrun_prob * 100) : "–"}%</p>
        <p className="text-xs mt-2">{ev.plan?.risk_note}</p></div>
      <div className="card md:col-span-2"><h2 className="font-medium mb-2">Venue and vendor shortlist</h2>
        <div className="grid sm:grid-cols-2 gap-3">{ev.vendors.map((v: any) => <div key={v.id} className="border border-line rounded p-3 text-sm">
          <b>{v.name}</b> <span className="text-xs">({v.kind})</span><div>{inr(v.cost_inr)}{v.capacity ? ` · seats ${v.capacity}` : ""}{v.av ? " · AV" : ""}{v.catering ? " · catering" : ""}</div>
          <p className="text-xs mt-1"><b>Why recommended:</b> {v.why || "Matches city and budget filters."}</p></div>)}</div></div>
    </section>
    <section className="card"><h2 className="font-medium mb-2">Agenda</h2>
      {conflicts.map((c, i) => <p key={i} className="text-sm text-red-700 mb-1">⚠ {c}</p>)}
      {agenda.map((a: any, i: number) => <div key={i} className="flex gap-4 text-sm border-t border-line py-1"><span className="w-28">{a.start}–{a.end}</span><span className="flex-1">{a.title}</span><span>{a.speaker} · {a.room}</span></div>)}</section>
  </div>);
}
