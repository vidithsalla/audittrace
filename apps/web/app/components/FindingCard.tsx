import type { AuditFinding } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";

export function FindingCard({ finding }: { finding: AuditFinding }) {
  return (
    <article className={`card finding ${finding.status}`}>
      <div className="actions" style={{ marginTop: 0 }}>
        <StatusBadge value={finding.status} />
        <span className="badge">{finding.severity}</span>
        <span className="badge">{finding.source}</span>
        {finding.evidence_validated ? <span className="badge pass">Evidence validated</span> : null}
        {finding.unsupported_finding ? <span className="badge insufficient_evidence">Unsupported evidence caught</span> : null}
      </div>
      <h3>{finding.question_key}</h3>
      <p className="muted">{finding.criterion_text}</p>
      {finding.status === "insufficient_evidence" ? (
        <p>
          <strong>Downgraded: insufficient evidence.</strong> Required evidence did not validate against the
          source synthetic note.
        </p>
      ) : null}
      <p>{finding.reason}</p>
      {finding.resolution ? <p className="muted">Resolution: {finding.resolution}</p> : null}
      {finding.validation_notes ? <p className="muted">{finding.validation_notes}</p> : null}
      {finding.evidence_spans.length ? (
        <div className="stack">
          {finding.evidence_spans.map((span, index) => (
            <div className="quote" key={`${finding.id}-${index}`}>
              <div className="actions" style={{ marginTop: 0 }}>
                <StatusBadge value={span.validation_status} />
                <span className="muted">
                  chars {span.start_char ?? "n/a"} to {span.end_char ?? "n/a"}
                </span>
              </div>
              <p>{span.quote}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">No evidence span required or provided.</p>
      )}
    </article>
  );
}
