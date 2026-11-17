"use client";
import { useEffect, useState } from "react";
import { j, post } from "../api";
export default function Approvals() {
  const [pending, setPending] = useState<any[]>([]); const [audit, setAudit] = useState<any[]>([]); const [edits, setEdits] = useState<Record<number, string>>({});
  const load = () => { j("/api/approvals").then(setPending); j("/api/audit").then(setAudit); }; useEffect(load, []);
  const decide = async (a: any, decision: string) => { let payload; if (decision === "edit") { try { payload = JSON.parse(edits[a.id] ?? JSON.stringify(a.payload)); } catch { alert("Payload is not valid JSON"); return; } }
    await post(`/api/approvals/${a.id}/decide`, { decision, payload }); load(); };
  return (<div className="space-y-6"><h1 className="text-2xl font-semibold">Pending AI actions</h1>
    {pending.length === 0 && <p className="text-sm">Nothing waiting. Create a brief to generate actions.</p>}
    {pending.map(a => <div key={a.id} className="card space-y-2"><div className="flex justify-between"><b>{a.kind.replace(/_/g, " ")}</b><span className="text-sm">Confidence {Math.round(a.confidence * 100)}%</span></div>
      <textarea className="w-full border border-line rounded p-2 font-mono text-xs h-28" defaultValue={JSON.stringify(a.payload, null, 2)} onChange={e => setEdits({ ...edits, [a.id]: e.target.value })} />
      <p className="text-xs">Sources: {a.citations.join("; ")}</p>
      <div className="flex gap-2"><button className="btn btn-primary" onClick={() => decide(a, "approve")}>Approve and execute</button>
        <button className="btn" onClick={() => decide(a, "edit")}>Edit and approve</button><button className="btn" onClick={() => decide(a, "reject")}>Reject</button></div></div>)}
    <h2 className="text-lg font-semibold">Audit log</h2>
    <table className="w-full text-sm card"><thead><tr className="text-left"><th>Time</th><th>Action</th><th>Decision</th><th>Actor</th></tr></thead>
      <tbody>{audit.map(l => <tr key={l.id} className="border-t border-line"><td>{new Date(l.ts + "Z").toLocaleString()}</td><td>#{l.action_id}</td><td>{l.decision}</td><td>{l.actor}</td></tr>)}</tbody></table></div>);
}
