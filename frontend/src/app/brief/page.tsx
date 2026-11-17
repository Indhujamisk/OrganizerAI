"use client";
import { useState } from "react";
import { API, inr } from "../api";
export default function Brief() {
  const [prompt, setPrompt] = useState("Plan a 200-person AI meetup in Coimbatore on 12 December with a ₹3,00,000 budget, 3 speakers, catering, and registration");
  const [file, setFile] = useState<File | null>(null); const [provider, setProvider] = useState("gemini");
  const [res, setRes] = useState<any>(null); const [busy, setBusy] = useState(false);
  const submit = async () => { setBusy(true); const f = new FormData(); f.append("prompt", prompt); f.append("provider", provider); if (file) f.append("file", file);
    setRes(await fetch(API + "/api/events/brief", { method: "POST", body: f }).then(r => r.json())); setBusy(false); };
  return (<div className="max-w-2xl space-y-4"><h1 className="text-2xl font-semibold">Describe your event</h1>
    <textarea className="w-full border border-line rounded p-3 h-32" value={prompt} onChange={e => setPrompt(e.target.value)} />
    <input type="file" accept=".pdf,image/*" onChange={e => setFile(e.target.files?.[0] || null)} />
    <div className="flex gap-3 items-center"><select value={provider} onChange={e => setProvider(e.target.value)} className="border border-line rounded px-2 py-1 bg-white">
      <option value="gemini">Gemini (cloud)</option><option value="ollama">Ollama (local, private)</option></select>
      <button className="btn btn-primary" disabled={busy} onClick={submit}>{busy ? "Planning…" : "Extract and plan"}</button></div>
    {res?.entities && <div className="card text-sm space-y-1"><h2 className="font-medium">What we understood</h2>
      <p>City: {res.entities.city} · Date: {res.entities.date} · Guests: {res.entities.headcount} · Budget: {inr(res.entities.budget_inr)} · Speakers: {res.entities.speakers}</p>
      <p>Sources: {res.sources.join(", ")}</p>
      {res.assumptions.map((a: string) => <p key={a} className="text-amber-700">Assumed: {a}</p>)}
      <a href="/approvals" className="btn btn-primary inline-block mt-2">Review pending actions</a></div>}</div>);
}
