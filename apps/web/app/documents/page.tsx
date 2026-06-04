import Link from "next/link";
import { getDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  try {
    const documents = await getDocuments();
    return (
      <>
        <section className="page-header">
          <p className="eyebrow">Synthetic notes</p>
          <h1>Documents</h1>
          <p className="muted">Seeded synthetic notes used to exercise audit findings and eval metrics.</p>
        </section>

        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Specialty</th>
                <th>Service code</th>
                <th>Provider</th>
                <th>Note type</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((document) => (
                <tr key={document.id}>
                  <td>{document.title}</td>
                  <td>{document.specialty}</td>
                  <td>{document.service_code || "n/a"}</td>
                  <td>{document.provider_id}</td>
                  <td>{document.note_type}</td>
                  <td>
                    <Link href={`/documents/${document.id}`}>View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </>
    );
  } catch (error) {
    return <div className="error">Could not load documents: {error instanceof Error ? error.message : "unknown error"}</div>;
  }
}
