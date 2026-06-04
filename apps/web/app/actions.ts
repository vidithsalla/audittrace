"use server";

import { redirect } from "next/navigation";
import { runAudit, runEval } from "@/lib/api";

export async function runAuditAction(formData: FormData) {
  const documentId = String(formData.get("document_id") || "");
  const questionSetVersionId = String(formData.get("question_set_version_id") || "");
  if (!documentId || !questionSetVersionId) {
    throw new Error("Document and question-set version are required.");
  }
  const audit = await runAudit(documentId, questionSetVersionId);
  if (!audit) {
    throw new Error("Audit run did not return a response.");
  }
  redirect(`/audits/${audit.audit_id}`);
}

export async function runEvalAction() {
  const evalRun = await runEval();
  if (!evalRun) {
    throw new Error("Eval run did not return a response.");
  }
  redirect(`/evals?eval_run_id=${evalRun.eval_run_id}`);
}
