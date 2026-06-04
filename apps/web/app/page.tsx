import Link from "next/link";
import { getDocuments, getLatestEval, getQuestionSets } from "@/lib/api";
import { MetricCard } from "./components/MetricCard";
import { RunEvalForm } from "./components/RunEvalForm";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  try {
    const [documents, questionSets, latestEval] = await Promise.all([
      getDocuments(),
      getQuestionSets(),
      getLatestEval(),
    ]);
    const versionCount = questionSets.reduce((total, set) => total + set.versions.length, 0);

    return (
      <>
        <section className="page-header">
          <p className="eyebrow">Synthetic data only</p>
          <h1>AuditTrace</h1>
          <p className="muted">
            Synthetic audit reliability prototype. Not medical advice, not affiliated with Brellium, and not a
            clinical compliance product.
          </p>
          <div className="actions">
            <Link className="button" href="/documents">
              View documents
            </Link>
            <Link className="button secondary" href="/question-sets">
              View question sets
            </Link>
            <RunEvalForm />
          </div>
        </section>

        <section className="grid grid-3">
          <MetricCard label="Documents" value={documents.length} />
          <MetricCard label="Question sets" value={questionSets.length} />
          <MetricCard label="Question-set versions" value={versionCount} />
        </section>

        <section className="panel" style={{ marginTop: 18 }}>
          <h2>Latest eval metrics</h2>
          {latestEval ? (
            <div className="grid grid-3">
              <MetricCard label="Total cases" value={latestEval.metrics.total_cases} />
              <MetricCard label="Unsupported finding rate" value={latestEval.metrics.unsupported_finding_rate} kind="percent" />
              <MetricCard label="Evidence span match rate" value={latestEval.metrics.evidence_span_match_rate} kind="percent" />
            </div>
          ) : (
            <p className="muted">No eval run yet. Run eval to populate reliability metrics.</p>
          )}
        </section>

        <section className="panel" style={{ marginTop: 18 }}>
          <h2>Reliability loop</h2>
          <p className="muted">
            Versioned question sets feed deterministic and mock narrative checks. Findings that require evidence must
            cite source text. Unsupported evidence fails closed to insufficient evidence, and evals measure that behavior.
          </p>
        </section>
      </>
    );
  } catch (error) {
    return <ApiErrorPanel error={error} />;
  }
}

function ApiErrorPanel({ error }: { error: unknown }) {
  return (
    <div className="error">
      <h1>Backend unavailable</h1>
      <p>Start the FastAPI backend and seed the database, then refresh this page.</p>
      <p className="muted">{error instanceof Error ? error.message : "Unknown API error"}</p>
    </div>
  );
}
