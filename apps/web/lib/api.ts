const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type FetchOptions = RequestInit & { allowNotFound?: boolean };

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T | null> {
  const { allowNotFound, ...fetchOptions } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...(fetchOptions.headers || {}),
    },
    cache: "no-store",
  });

  if (response.status === 404 && allowNotFound) {
    return null;
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
    } catch {
      // Keep the status text if the response is not JSON.
    }
    throw new ApiError(detail || "API request failed", response.status);
  }
  return (await response.json()) as T;
}

export type DocumentListItem = {
  id: string;
  title: string;
  provider_id: string;
  provider_name: string;
  specialty: string;
  service_code: string | null;
  state: string;
  date_of_service: string | null;
  note_type: string;
};

export type DocumentDetail = {
  id: string;
  title: string;
  metadata: {
    provider_id: string;
    provider_name: string;
    specialty: string;
    service_code: string | null;
    payer: string | null;
    state: string;
    date_of_service: string | null;
    note_type: string;
  };
  body: string;
};

export type QuestionSetSummary = {
  id: string;
  slug: string;
  name: string;
  specialty: string;
  versions: QuestionSetVersionSummary[];
};

export type QuestionSetVersionSummary = {
  id: string;
  version: string;
  status: string;
  change_summary: string | null;
};

export type QuestionSetVersionDetail = {
  id: string;
  question_set: {
    id: string;
    slug: string;
    name: string;
  };
  version: string;
  status: string;
  questions: Question[];
};

export type Question = {
  id: string;
  question_key: string;
  criterion_text: string;
  severity: string;
  check_type: string;
  requires_evidence: boolean;
  deterministic_rule: string | null;
};

export type EvidenceSpan = {
  quote: string;
  start_char: number | null;
  end_char: number | null;
  validation_status: string;
};

export type AuditFinding = {
  id: string;
  question_id: string;
  question_key: string;
  criterion_text: string;
  status: string;
  severity: string;
  reason: string;
  resolution: string | null;
  confidence: number | null;
  source: string;
  evidence_validated: boolean;
  unsupported_finding: boolean;
  validation_notes: string | null;
  evidence_spans: EvidenceSpan[];
};

export type AuditLog = {
  id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AuditRunSummary = {
  id: string;
  status: string;
  model_mode: string;
  latency_ms: number | null;
  summary: Record<string, number>;
  created_at: string;
};

export type AuditRunResponse = {
  audit_id: string;
  audit_run_id: string;
  document_id: string;
  question_set_version_id: string;
  status: string;
  summary: Record<string, number>;
  latency_ms: number | null;
  findings: AuditFinding[];
};

export type AuditDetail = {
  id: string;
  document: {
    id: string;
    title: string;
    body: string | null;
  };
  question_set_version: {
    id: string;
    slug: string;
    version: string;
  };
  status: string;
  model_mode: string;
  summary: Record<string, number>;
  latency_ms: number | null;
  findings: AuditFinding[];
  logs: AuditLog[];
};

export type EvalMetrics = {
  total_cases: number;
  total_questions_evaluated: number;
  critical_issue_recall: number | null;
  false_positive_rate: number | null;
  unsupported_finding_rate: number | null;
  evidence_span_match_rate: number | null;
  insufficient_evidence_rate: number | null;
  regression_failures_by_question_set_version: Record<string, number>;
  average_audit_latency_ms: number | null;
};

export type EvalFailurePreview = {
  eval_case_id: string;
  case_key: string;
  audit_run_id: string | null;
  errors: Record<string, unknown>[];
};

export type EvalRunResponse = {
  eval_run_id: string;
  status: string;
  metrics: EvalMetrics;
  failures_preview: EvalFailurePreview[];
  result_count: number;
};

export type EvalRunDetail = {
  id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  metrics: EvalMetrics;
  failures_preview: EvalFailurePreview[];
  results: {
    id: string;
    eval_case_id: string;
    case_key: string;
    audit_run_id: string | null;
    passed: boolean;
    expected: Record<string, unknown>[];
    actual: Record<string, unknown>[];
    errors: Record<string, unknown>[];
    latency_ms: number | null;
  }[];
};

export async function getDocuments() {
  const payload = await request<{ documents: DocumentListItem[] }>("/documents");
  return payload?.documents || [];
}

export async function getDocument(id: string) {
  return request<DocumentDetail>(`/documents/${id}`);
}

export async function getQuestionSets() {
  const payload = await request<{ question_sets: QuestionSetSummary[] }>("/question-sets");
  return payload?.question_sets || [];
}

export async function getQuestionSetVersion(id: string) {
  return request<QuestionSetVersionDetail>(`/question-sets/${id}`);
}

export async function runAudit(documentId: string, questionSetVersionId: string) {
  return request<AuditRunResponse>("/audits/run", {
    method: "POST",
    body: JSON.stringify({
      document_id: documentId,
      question_set_version_id: questionSetVersionId,
      model_mode: "mock",
    }),
  });
}

export async function getAudit(id: string) {
  return request<AuditDetail>(`/audits/${id}`);
}

export async function getDocumentAudits(documentId: string) {
  const payload = await request<{ audits: AuditRunSummary[] }>(`/documents/${documentId}/audits`);
  return payload?.audits || [];
}

export async function runEval() {
  return request<EvalRunResponse>("/evals/run", {
    method: "POST",
    body: JSON.stringify({ model_mode: "mock" }),
  });
}

export async function getLatestEval() {
  return request<EvalRunDetail>("/evals/latest", { allowNotFound: true });
}

export async function getEval(id: string) {
  return request<EvalRunDetail>(`/evals/${id}`);
}
