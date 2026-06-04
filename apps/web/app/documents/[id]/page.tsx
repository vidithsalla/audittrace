import Link from "next/link";
import { runAuditAction } from "@/app/actions";
import { getDocument, getDocumentAudits, getQuestionSets } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const [document, questionSets, audits] = await Promise.all([
      getDocument(id),
      getQuestionSets(),
      getDocumentAudits(id),
    ]);
    if (!document) {
      return <div className="error">Document not found.</div>;
    }
    const versions = questionSets.flatMap((set) =>
      set.versions.map((version) => ({
        ...version,
        label: `${set.slug}-${version.version}`,
        specialty: set.specialty,
      })),
    );

    return (
      <>
        <section className="page-header">
          <p className="eyebrow">Synthetic note</p>
          <h1>{document.title}</h1>
          <p className="muted">Synthetic data only. Use a versioned question set to run the mock audit runner.</p>
        </section>

        <div className="split">
          <section className="stack">
            <div className="panel">
              <h2>Metadata</h2>
              <table>
                <tbody>
                  <tr>
                    <th>Provider</th>
                    <td>{document.metadata.provider_name}</td>
                  </tr>
                  <tr>
                    <th>Specialty</th>
                    <td>{document.metadata.specialty}</td>
                  </tr>
                  <tr>
                    <th>Service code</th>
                    <td>{document.metadata.service_code || "n/a"}</td>
                  </tr>
                  <tr>
                    <th>Date of service</th>
                    <td>{document.metadata.date_of_service || "n/a"}</td>
                  </tr>
                  <tr>
                    <th>Note type</th>
                    <td>{document.metadata.note_type}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <pre className="pre">{document.body}</pre>
          </section>

          <aside className="stack">
            <div className="panel">
              <h2>Run audit</h2>
              <form action={runAuditAction} className="stack">
                <input type="hidden" name="document_id" value={document.id} />
                <label htmlFor="question_set_version_id">Question-set version</label>
                <select id="question_set_version_id" name="question_set_version_id" defaultValue={versions[0]?.id}>
                  {versions.map((version) => (
                    <option key={version.id} value={version.id}>
                      {version.label} ({version.status})
                    </option>
                  ))}
                </select>
                <button type="submit">Run mock audit</button>
              </form>
            </div>

            <div className="panel">
              <h2>Prior audits</h2>
              {audits.length ? (
                <div className="stack">
                  {audits.map((audit) => (
                    <div className="card" key={audit.id}>
                      <Link href={`/audits/${audit.id}`}>Audit {audit.id.slice(0, 8)}</Link>
                      <p className="muted">
                        {audit.status} · {audit.model_mode} · {audit.summary.total ?? 0} findings
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No audits have been run for this document yet.</p>
              )}
            </div>
          </aside>
        </div>
      </>
    );
  } catch (error) {
    return <div className="error">Could not load document: {error instanceof Error ? error.message : "unknown error"}</div>;
  }
}
