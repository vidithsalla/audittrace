import { FindingCard } from "@/app/components/FindingCard";
import { MetricCard } from "@/app/components/MetricCard";
import { StatusBadge } from "@/app/components/StatusBadge";
import { getAudit } from "@/lib/api";
import { titleize } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function AuditDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const audit = await getAudit(id);
    if (!audit) {
      return <div className="error">Audit not found.</div>;
    }
    const groups = groupFindings(audit.findings);

    return (
      <>
        <section className="page-header">
          <p className="eyebrow">Audit detail</p>
          <h1>{audit.document.title}</h1>
          <div className="actions">
            <StatusBadge value={audit.status} />
            <span className="badge">Mock audit runner</span>
            <span className="badge">
              {audit.question_set_version.slug}-{audit.question_set_version.version}
            </span>
          </div>
        </section>

        <section className="grid grid-3">
          <MetricCard label="Findings" value={audit.summary.total ?? audit.findings.length} />
          <MetricCard label="Critical failures" value={audit.summary.critical_failures ?? 0} />
          <MetricCard label="Unsupported findings caught" value={audit.summary.unsupported_findings ?? 0} />
        </section>

        <div className="split" style={{ marginTop: 18 }}>
          <section className="stack">
            <h2>Source synthetic note</h2>
            <pre className="pre">{audit.document.body || "No document body returned."}</pre>
          </section>

          <section className="stack">
            <section className="panel">
              <h2>Audit log timeline</h2>
              {audit.logs.length ? (
                <ol className="timeline">
                  {audit.logs.map((log) => (
                    <li key={log.id}>
                      <strong>{log.action}</strong>
                      <span className="muted">
                        {log.actor} · {new Date(log.created_at).toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="muted">No audit logs returned for this audit.</p>
              )}
            </section>

            <h2>Findings</h2>
            {Object.entries(groups).map(([groupName, findings]) => (
              <div className="stack" key={groupName}>
                <h3>{titleize(groupName)}</h3>
                {findings.map((finding) => (
                  <FindingCard finding={finding} key={finding.id} />
                ))}
              </div>
            ))}
          </section>
        </div>
      </>
    );
  } catch (error) {
    return <div className="error">Could not load audit: {error instanceof Error ? error.message : "unknown error"}</div>;
  }
}

function groupFindings<T extends { status: string; severity: string }>(findings: T[]) {
  const order = ["insufficient_evidence", "fail", "needs_review", "pass"];
  return findings
    .slice()
    .sort((a, b) => `${a.status}-${a.severity}`.localeCompare(`${b.status}-${b.severity}`))
    .reduce<Record<string, T[]>>((groups, finding) => {
      const key = finding.status;
      groups[key] = groups[key] || [];
      groups[key].push(finding);
      return groups;
    }, Object.fromEntries(order.map((key) => [key, []])) as Record<string, T[]>);
}
