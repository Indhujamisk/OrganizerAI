import "./globals.css";
import Link from "next/link";
export const metadata = { title: "OrganizerAI" };
export default function Root({ children }: { children: React.ReactNode }) {
  const nav = [["/", "Control room"], ["/brief", "New brief"], ["/approvals", "Approvals"], ["/attendee", "Attendee view"], ["/eval", "Evaluation"]];
  return (<html lang="en"><body>
    <header className="bg-ink text-white"><nav className="max-w-6xl mx-auto flex gap-5 items-center px-4 py-3 flex-wrap">
      <span className="font-semibold mr-4 text-sun">OrganizerAI</span>
      {nav.map(([h, l]) => <Link key={h} href={h} className="text-sm hover:underline">{l}</Link>)}
    </nav></header>
    <main className="max-w-6xl mx-auto p-4">{children}</main></body></html>);
}
