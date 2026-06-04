from audittrace_api.models import Question, SyntheticDocument
from audittrace_api.services.audit_types import DraftEvidenceSpan, DraftFinding, LlmAuditFinding


def _contains(text: str, *needles: str) -> bool:
    lower_text = text.lower()
    return any(needle.lower() in lower_text for needle in needles)


def _finding(status: str, reason: str, quote: str, resolution: str | None = None, confidence: float = 0.82) -> LlmAuditFinding:
    return LlmAuditFinding(
        status=status,
        reason=reason,
        resolution=resolution,
        confidence=confidence,
        evidence_spans=[{"quote": quote}],
    )


class MockModelClient:
    """Deterministic stand-in for the future structured LLM path."""

    def audit_question(self, document: SyntheticDocument, question: Question) -> LlmAuditFinding:
        body = document.body
        title = document.title.lower()
        key = question.question_key

        if key == "protocol_change_rationale":
            if "adversarial invalid evidence" in title:
                return _finding(
                    "fail",
                    "The synthetic note mentions a protocol adjustment without a validated reason.",
                    "The protocol was changed due to aggression.",
                    "Add a source-backed, patient-specific rationale for the protocol change.",
                    confidence=0.74,
                )
            if "Protocol was adjusted during the session." in body:
                return _finding(
                    "fail",
                    "The note states that the protocol changed but does not explain why the change was needed.",
                    "Protocol was adjusted during the session.",
                    "Add patient-specific rationale tied to observed response and treatment goals.",
                )
            if _contains(body, "because the prior prompt delay", "because the prior sequence", "because the prior prompt level"):
                quote = _first_existing(
                    body,
                    [
                        "The transition protocol was modified because the prior prompt delay led to escalation and task refusal.",
                        "The provider changed the prompt hierarchy because the prior sequence produced repeated errors during acquisition trials.",
                        "The teaching protocol was modified because the prior prompt level was no longer effective for the target program.",
                    ],
                )
                return _finding("pass", "The note provides a synthetic rationale for the protocol change.", quote)
            return _finding(
                "needs_review",
                "The note references protocol work but the rationale is generic.",
                "The protocol was reviewed during skill acquisition programming.",
                "Clarify the observed trigger and patient-specific reason for the change.",
                confidence=0.68,
            )

        if key == "individualized_observation":
            if _contains(body, "participated appropriately and responded well"):
                return _finding(
                    "fail" if question.version.version == "v2" else "needs_review",
                    "The response language is generic and does not describe a patient-specific response.",
                    "The client participated appropriately and responded well to the updated teaching steps.",
                    "Add patient-specific response detail from the synthetic session.",
                    confidence=0.76,
                )
            if _contains(body, "completed two transitions with one verbal prompt", "completed three matching trials", "completed several transition tasks"):
                quote = _first_existing(
                    body,
                    [
                        "After the modification, the client completed two transitions with one verbal prompt and no escalation.",
                        "The client completed three matching trials with reduced latency after the change.",
                        "The client completed several transition tasks with fewer prompts by the end of session.",
                    ],
                )
                return _finding("pass", "The note includes a patient-specific synthetic response.", quote)
            return _finding(
                "needs_review",
                "The note does not clearly individualize the synthetic client response.",
                "The client completed practice activities with variable prompting.",
                "Add patient-specific response detail.",
                confidence=0.66,
            )

        if key == "treatment_plan_linkage":
            if _contains(body, "treatment plan", "transition goals", "review transition data", "review data next session"):
                quote = _first_existing(
                    body,
                    [
                        "Review transition data next session and continue the modified protocol if refusal remains below baseline.",
                        "Continue caregiver training aligned to transition goals in the treatment plan.",
                        "Continue with the updated teaching procedure and review data next session.",
                    ],
                )
                return _finding("pass", "The note links activity to a synthetic plan or goal.", quote)
            return _finding(
                "needs_review",
                "The note has limited treatment-plan linkage.",
                "Continue monitoring protocol response during the next session.",
                "Tie the synthetic documentation to a stated plan goal.",
                confidence=0.7,
            )

        if key == "caregiver_training_content":
            return _finding(
                "pass",
                "The note describes caregiver training content.",
                "The provider reviewed visual schedule setup and transition prompting steps with the caregiver.",
            )

        if key == "caregiver_skill_uptake":
            return _finding(
                "fail",
                "The note says the caregiver listened but does not document skill practice or uptake.",
                "Caregiver listened to the explanation and asked questions about home routines.",
                "Document synthetic caregiver demonstration, practice, or feedback.",
            )

        if key == "terminal_prognosis_support":
            if _contains(body, "weak and needs support"):
                return _finding(
                    "fail",
                    "The prognosis support is vague and does not include measurable patient-specific decline.",
                    "Patient remains appropriate for hospice services. Patient is weak and needs support with daily activities.",
                    "Add synthetic measurable decline details if available.",
                )
            return _finding(
                "needs_review",
                "The note has limited prognosis support.",
                "Continue current plan.",
                "Add patient-specific prognosis support.",
                confidence=0.64,
            )

        if key == "patient_specific_decline":
            if _contains(body, "No new measurements were documented"):
                return _finding(
                    "fail",
                    "The note does not document patient-specific decline indicators.",
                    "No new measurements were documented.",
                    "Add synthetic decline indicators such as functional changes, intake, or measurements.",
                )
            return _finding("needs_review", "Patient-specific decline detail is limited.", "Continue current plan.", confidence=0.62)

        if key == "plan_of_care_alignment":
            if _contains(body, "did not address dyspnea monitoring or caregiver education"):
                return _finding(
                    "fail",
                    "The visit focus does not align with the stated synthetic plan of care focus.",
                    "The visit focused only on supply inventory and did not address dyspnea monitoring or caregiver education.",
                    "Align the synthetic visit documentation with the plan of care.",
                )
            return _finding("pass", "The note does not show a clear plan-of-care mismatch.", "Continue current plan.")

        if key == "copy_forward_risk":
            if _contains(body, "Continue current plan."):
                return _finding(
                    "needs_review",
                    "The note uses generic continuation language that may need review.",
                    "Continue current plan.",
                    "Replace generic copied-forward language with synthetic visit-specific detail.",
                    confidence=0.7,
                )
            return _finding("pass", "No obvious copy-forward risk phrase was detected.", "Plan:")

        if key == "medical_necessity_support":
            return _finding(
                "fail",
                "The session activities are generic and do not support patient-specific medical necessity.",
                "The session included supportive discussion and review of the weekly schedule.",
                "Add synthetic patient-specific symptoms or functional impairment tied to the session.",
            )

        if key == "session_focus_matches_plan":
            return _finding(
                "needs_review",
                "The plan linkage is generic.",
                "Continue supportive sessions.",
                "Document how the session focus matches synthetic plan goals.",
                confidence=0.66,
            )

        if key == "risk_or_symptom_update":
            return _finding("pass", "The note includes a current synthetic risk update.", "No acute safety concern was reported in this synthetic note.")

        return LlmAuditFinding(
            status="needs_review",
            reason="No mock narrative heuristic is configured for this criterion.",
            resolution="Add a mock heuristic before relying on this criterion in demos.",
            confidence=0.5,
            evidence_spans=[],
        )


def _first_existing(body: str, quotes: list[str]) -> str:
    for quote in quotes:
        if quote in body:
            return quote
    return quotes[0]


def run_mock_narrative_check(document: SyntheticDocument, question: Question, client: MockModelClient | None = None) -> DraftFinding:
    model_client = client or MockModelClient()
    llm_finding = model_client.audit_question(document, question)
    return DraftFinding(
        question_id=question.id,
        status=llm_finding.status,
        severity=question.severity,
        reason=llm_finding.reason,
        resolution=llm_finding.resolution,
        confidence=llm_finding.confidence,
        source="llm",
        requires_evidence=question.requires_evidence,
        evidence_spans=[DraftEvidenceSpan(quote=span.quote) for span in llm_finding.evidence_spans],
    )
