import { getQuestionSetVersion, getQuestionSets } from "@/lib/api";
import type { QuestionSetVersionDetail } from "@/lib/api";
import { StatusBadge } from "../components/StatusBadge";

export const dynamic = "force-dynamic";

export default async function QuestionSetsPage() {
  try {
    const questionSets = await getQuestionSets();
    const versionDetails = await Promise.all(
      questionSets.flatMap((set) => set.versions.map((version) => getQuestionSetVersion(version.id))),
    );
    const detailById = new Map(
      versionDetails
        .filter((detail): detail is QuestionSetVersionDetail => detail !== null)
        .map((detail) => [detail.id, detail]),
    );

    return (
      <>
        <section className="page-header">
          <p className="eyebrow">Versioned criteria</p>
          <h1>Question Sets</h1>
          <p className="muted">Criteria are versioned so audits and evals can be traced to a specific question set.</p>
        </section>

        <div className="stack">
          {questionSets.map((set) => (
            <section className="panel" key={set.id}>
              <h2>{set.name}</h2>
              <p className="muted">
                {set.slug} · {set.specialty}
              </p>
              <div className="stack">
                {set.versions.map((version) => {
                  const detail = detailById.get(version.id);
                  return (
                    <div className="card" key={version.id}>
                      <div className="actions" style={{ marginTop: 0 }}>
                        <span className="badge">Question-set version {version.version}</span>
                        <StatusBadge value={version.status} />
                        <span className="badge">{detail?.questions.length ?? 0} questions</span>
                      </div>
                      <p>{version.change_summary}</p>
                      {detail ? (
                        <table>
                          <thead>
                            <tr>
                              <th>Question key</th>
                              <th>Type</th>
                              <th>Severity</th>
                              <th>Requires evidence</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detail.questions.map((question) => (
                              <tr key={question.id}>
                                <td>{question.question_key}</td>
                                <td>{question.check_type}</td>
                                <td>{question.severity}</td>
                                <td>{question.requires_evidence ? "yes" : "no"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </>
    );
  } catch (error) {
    return <div className="error">Could not load question sets: {error instanceof Error ? error.message : "unknown error"}</div>;
  }
}
