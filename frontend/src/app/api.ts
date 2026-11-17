export const API = process.env.NEXT_PUBLIC_API || "http://localhost:8000";
export const j = (p: string, o?: RequestInit) => fetch(API + p, o).then(r => r.json());
export const post = (p: string, b: any) => j(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
export const inr = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");
