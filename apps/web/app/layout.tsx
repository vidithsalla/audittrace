import Link from "next/link";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AuditTrace",
  description: "Synthetic audit reliability prototype",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <nav className="nav" aria-label="Primary navigation">
              <Link className="brand" href="/">
                AuditTrace
              </Link>
              <Link href="/documents">Documents</Link>
              <Link href="/question-sets">Question Sets</Link>
              <Link href="/evals">Evals</Link>
            </nav>
          </header>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
