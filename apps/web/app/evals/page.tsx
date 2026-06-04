import Link from "next/link";
import { RunEvalForm } from "@/app/components/RunEvalForm";
import { MetricCard } from "@/app/components/MetricCard";
import { getEval, getLatestEval } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EvalsPage({
  searchParams,
}: {
  searchParams: Promise<{ eval_run_id?: string }>;
}) {
  const { eval_run_id: evalRunId } = await searchParams;
  try {
    const evalRun = evalRunId ? await getEval(evalRunId) : await getLatestEval();
    return (
      <>
        <section className="page-header">
          <p className="eyebrow">Reliability metrics</p>
          <h1>Evals</h1>
          <p className="muted">
            Runs seeded synthetic cases through the same audit path and compares actual findings to expected outcomes.
          </p>
          <div className="actions">
            <RunEvalForm />
          </div>
        </section>

        {evalRun ? (
          <>
            <section className="grid grid-3">
              <MetricCard label="Total cases" value={evalRun.metrics.total_cases} />
              <MetricCard label="Questions evaluated" value={evalRun.metrics.total_questions_evaluated} />
              <MetricCard label="Critical issue recall" value={evalRun.metrics.critical_issue_recall} kind="percent" />
              <MetricCard label="False positive rate" value={evalRun.metrics.false_positive_rate} kind="percent" />
              <MetricCard label="Unsupported finding rate" value={evalRun.metrics.unsupported_finding_rate} kind="percent" />
              <MetricCard label="Evidence span match rate" value={evalRun.metrics.evidence_span_match_rate} kind="percent" />
              <MetricCard label="Insufficient evidence rate" value={evalRun.metrics.insufficient_evidence_rate} kind="percent" />
              <MetricCard label="Average audit latency" value={evalRun.metrics.average_audit_latency_ms} kind="ms" />
            </section>

            <section className="panel" style={{ marginTop: 18 }}>
              <h2>Failures preview</h2>
              {evalRun.failures_preview.length ? (
                <table>
                  <thead>
                    <tr>
                      <th>Case</th>
                      <th>Audit</th>
                      <th>Errors</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evalRun.failures_preview.map((failure) => (
                      <tr key={failure.eval_case_id}>
                        <td>{failure.case_key}</td>
                        <td>
                          {failure.audit_run_id ? <Link href={`/audits/${failure.audit_run_id}`}>Open audit</Link> : "n/a"}
                        </td>
                        <td>
                          <pre>{JSON.stringify(failure.errors, null, 2)}</pre>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="muted">No failed comparisons in the latest eval run.</p>
              )}
            </section>

            <section className="panel" style={{ marginTop: 18 }}>
              <h2>Regression failures by question-set version</h2>
              {Object.keys(evalRun.metrics.regression_failures_by_question_set_version).length ? (
                <pre>{JSON.stringify(evalRun.metrics.regression_failures_by_question_set_version, null, 2)}</pre>
              ) : (
                <p className="muted">No regression failures grouped for this run.</p>
              )}
            </section>
          </>
        ) : (
          <div className="panel">
            <p className="muted">No eval run exists yet. Run eval in mock mode to populate metrics.</p>
          </div>
        )}
      </>
    );
  } catch (error) {
    return <div className="error">Could not load evals: {error instanceof Error ? error.message : "unknown error"}</div>;
  }
}
