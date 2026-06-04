from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from audittrace_api.db import Base, SessionLocal, engine
from audittrace_api.models import (
    AuditLog,
    DocumentChunk,
    EvalCase,
    Provider,
    Question,
    QuestionSet,
    QuestionSetVersion,
    SyntheticDocument,
)


SYNTHETIC_NOTICE = "Synthetic data notice: This note is fictional and contains no real patient information."


PROVIDERS = [
    ("prov_aba_001", "Synthetic ABA Provider 1", "aba", "IN"),
    ("prov_aba_002", "Synthetic ABA Provider 2", "aba", "IN"),
    ("prov_aba_003", "Synthetic ABA Provider 3", "aba", "CA"),
    ("prov_hospice_001", "Synthetic Hospice Provider 1", "hospice", "TX"),
    ("prov_hospice_002", "Synthetic Hospice Provider 2", "hospice", "FL"),
    ("prov_bh_001", "Synthetic Behavioral Health Provider 1", "behavioral_health", "NY"),
    ("prov_bh_002", "Synthetic Behavioral Health Provider 2", "behavioral_health", "CA"),
    ("prov_bh_003", "Synthetic Behavioral Health Provider 3", "behavioral_health", "PA"),
]


QUESTION_SET_DEFS = [
    {
        "slug": "aba-97155",
        "name": "ABA 97155 Protocol Modification Audit",
        "specialty": "aba",
        "description": "Synthetic criteria for ABA protocol modification documentation.",
        "versions": [
            ("v1", "active", "Initial synthetic 97155 criteria"),
            ("v2", "active", "Stricter rationale and individualized observation criteria"),
        ],
    },
    {
        "slug": "aba-97156",
        "name": "ABA 97156 Caregiver Training Audit",
        "specialty": "aba",
        "description": "Synthetic criteria for caregiver training documentation.",
        "versions": [("v1", "active", "Initial synthetic 97156 criteria")],
    },
    {
        "slug": "hospice-eligibility",
        "name": "Hospice Eligibility Documentation Audit",
        "specialty": "hospice",
        "description": "Synthetic criteria for hospice eligibility documentation review.",
        "versions": [("v1", "active", "Initial synthetic hospice eligibility criteria")],
    },
    {
        "slug": "behavioralhealth-mednec",
        "name": "Behavioral Health Medical Necessity Audit",
        "specialty": "behavioral_health",
        "description": "Synthetic criteria for behavioral health medical necessity documentation.",
        "versions": [("v1", "active", "Initial synthetic behavioral health criteria")],
    },
]


QUESTION_DEFS = {
    ("aba-97155", "v1"): [
        ("missing_signature", "The note includes a dated provider signature.", "critical", "deterministic", False, "missing_signature", None),
        ("missing_credential", "The provider credential is documented with the signature or provider field.", "critical", "deterministic", False, "missing_credential", None),
        ("duration_unit_mismatch", "Billed units match documented duration using 15-minute units.", "critical", "deterministic", False, "duration_unit_mismatch", None),
        ("protocol_change_rationale", "The note explains why a protocol modification was necessary.", "critical", "llm", True, None, "Look for a patient-specific reason for the protocol change."),
        ("treatment_plan_linkage", "The note links the session activities to the treatment plan.", "warning", "llm", True, None, "Look for treatment-plan linkage, not general session activity."),
        ("individualized_observation", "The note includes individualized observations of the synthetic client response.", "warning", "llm", True, None, "Look for patient-specific response, not generic participation."),
    ],
    ("aba-97155", "v2"): [
        ("missing_signature", "The note includes a dated provider signature.", "critical", "deterministic", False, "missing_signature", None),
        ("missing_credential", "The provider credential is documented with the signature or provider field.", "critical", "deterministic", False, "missing_credential", None),
        ("duration_unit_mismatch", "Billed units match documented duration using 15-minute units.", "critical", "deterministic", False, "duration_unit_mismatch", None),
        ("protocol_change_rationale", "The note explains why the protocol changed and what observed behavior triggered it.", "critical", "llm", True, None, "Require both reason and observed trigger."),
        ("treatment_plan_linkage", "The note links the session activities to the treatment plan.", "warning", "llm", True, None, "Look for treatment-plan linkage, not general session activity."),
        ("individualized_observation", "The note includes patient-specific response, not generic participation.", "warning", "llm", True, None, "Fail generic response language."),
    ],
    ("aba-97156", "v1"): [
        ("missing_signature", "The note includes a dated provider signature.", "critical", "deterministic", False, "missing_signature", None),
        ("caregiver_present", "The note documents that a caregiver was present for training.", "warning", "deterministic", False, "missing_required_section", "Caregiver:"),
        ("caregiver_training_content", "The note documents what caregiver training content was covered.", "critical", "llm", True, None, "Look for specific caregiver training content."),
        ("caregiver_skill_uptake", "The note documents caregiver skill uptake or performance during training.", "warning", "llm", True, None, "Look for caregiver practice, demonstration, or feedback."),
        ("treatment_plan_linkage", "The note links caregiver training to the treatment plan.", "warning", "llm", True, None, "Look for treatment-plan linkage."),
    ],
    ("hospice-eligibility", "v1"): [
        ("missing_signature", "The note includes a dated provider signature.", "critical", "deterministic", False, "missing_signature", None),
        ("face_to_face_documented", "The note documents whether a face-to-face encounter occurred when relevant.", "warning", "deterministic", False, "missing_required_section", "Face-to-Face:"),
        ("terminal_prognosis_support", "The note supports the terminal prognosis statement with patient-specific documentation.", "critical", "llm", True, None, "Look for measurable, patient-specific prognosis support."),
        ("patient_specific_decline", "The note documents patient-specific decline rather than generic weakness.", "critical", "llm", True, None, "Look for specific decline indicators."),
        ("plan_of_care_alignment", "The note aligns the visit findings with the plan of care.", "warning", "llm", True, None, "Look for consistency with the plan of care."),
        ("copy_forward_risk", "The note avoids repeated generic language that creates copy-forward risk.", "warning", "llm", True, None, "Look for generic repeated language."),
    ],
    ("behavioralhealth-mednec", "v1"): [
        ("missing_signature", "The note includes a dated provider signature.", "critical", "deterministic", False, "missing_signature", None),
        ("medical_necessity_support", "The note supports medical necessity with patient-specific symptoms or functional impairment.", "critical", "llm", True, None, "Look for patient-specific symptoms or impairment."),
        ("session_focus_matches_plan", "The documented session focus matches the synthetic plan goals.", "warning", "llm", True, None, "Look for alignment with plan goals."),
        ("risk_or_symptom_update", "The note includes a current risk or symptom update.", "warning", "llm", True, None, "Look for current risk or symptom update."),
    ],
}


@dataclass(frozen=True)
class Scenario:
    category: str
    count: int
    provider_external_id: str
    question_set_slug: str
    version: str
    service_code: str | None
    note_type: str
    title: str
    primary_issue: str | None
    expected_status: str


SCENARIOS = [
    Scenario("aba_97155_clean_pass", 4, "prov_aba_002", "aba-97155", "v1", "97155", "progress_note", "ABA 97155 clean pass synthetic note", None, "pass"),
    Scenario("aba_97155_missing_rationale", 5, "prov_aba_001", "aba-97155", "v1", "97155", "progress_note", "ABA 97155 missing rationale synthetic note", "protocol_change_rationale", "fail"),
    Scenario("aba_97155_duration_mismatch", 4, "prov_aba_003", "aba-97155", "v1", "97155", "progress_note", "ABA 97155 duration mismatch synthetic note", "duration_unit_mismatch", "fail"),
    Scenario("aba_97155_v1_pass_v2_fail", 4, "prov_aba_002", "aba-97155", "v2", "97155", "progress_note", "ABA 97155 v2 stricter observation synthetic note", "individualized_observation", "fail"),
    Scenario("aba_97156_missing_uptake", 5, "prov_aba_001", "aba-97156", "v1", "97156", "progress_note", "ABA 97156 missing caregiver uptake synthetic note", "caregiver_skill_uptake", "fail"),
    Scenario("hospice_vague_prognosis", 5, "prov_hospice_001", "hospice-eligibility", "v1", None, "cti", "Hospice vague prognosis synthetic note", "terminal_prognosis_support", "fail"),
    Scenario("hospice_poc_mismatch", 4, "prov_hospice_002", "hospice-eligibility", "v1", None, "nursing_note", "Hospice plan-of-care mismatch synthetic note", "plan_of_care_alignment", "fail"),
    Scenario("bh_weak_mednec", 4, "prov_bh_001", "behavioralhealth-mednec", "v1", None, "progress_note", "Behavioral health weak medical necessity synthetic note", "medical_necessity_support", "fail"),
    Scenario("adversarial_invalid_evidence", 3, "prov_aba_003", "aba-97155", "v1", "97155", "progress_note", "Adversarial invalid evidence synthetic note", "protocol_change_rationale", "insufficient_evidence"),
]


def _note_body(category: str, provider_name: str, patient_id: str, dos: date, index: int) -> str:
    if category == "aba_97155_clean_pass":
        return f"""{SYNTHETIC_NOTICE}

Service Code: 97155
Date of Service: {dos.isoformat()}
Provider: {provider_name}, BCBA
Client: {patient_id}
Duration: 45 minutes
Billed Units: 3

Session Summary:
The provider observed increased refusal behavior during transition from preferred to non-preferred tasks compared with the prior two sessions.

Intervention:
The transition protocol was modified because the prior prompt delay led to escalation and task refusal. The provider shortened the initial demand interval and added a visual countdown before the transition.

Response:
After the modification, the client completed two transitions with one verbal prompt and no escalation.

Plan:
Review transition data next session and continue the modified protocol if refusal remains below baseline.

Provider Signature: {provider_name}, BCBA
"""
    if category == "aba_97155_missing_rationale":
        return f"""{SYNTHETIC_NOTICE}

Service Code: 97155
Date of Service: {dos.isoformat()}
Provider: {provider_name}, BCBA
Client: {patient_id}
Duration: 60 minutes
Billed Units: 4

Session Summary:
The provider observed the technician implementing the current behavior reduction protocol during table work and transition activities.

Intervention:
Protocol was adjusted during the session. The technician was instructed to use a shorter prompt delay and provide reinforcement after two consecutive correct responses.

Response:
The client completed several transition tasks with fewer prompts by the end of session.

Plan:
Continue monitoring protocol response during the next session.

Provider Signature: {provider_name}, BCBA
"""
    if category == "aba_97155_duration_mismatch":
        return f"""{SYNTHETIC_NOTICE}

Service Code: 97155
Date of Service: {dos.isoformat()}
Provider: {provider_name}, BCBA
Client: {patient_id}
Duration: 60 minutes
Billed Units: 5

Session Summary:
The protocol change was reviewed after the client showed increased latency during matching tasks.

Intervention:
The provider changed the prompt hierarchy because the prior sequence produced repeated errors during acquisition trials.

Response:
The client completed three matching trials with reduced latency after the change.

Plan:
Continue collecting acquisition data next visit.

Provider Signature: {provider_name}, BCBA
"""
    if category == "aba_97155_v1_pass_v2_fail":
        return f"""{SYNTHETIC_NOTICE}

Service Code: 97155
Date of Service: {dos.isoformat()}
Provider: {provider_name}, BCBA
Client: {patient_id}
Duration: 30 minutes
Billed Units: 2

Session Summary:
The protocol was reviewed during skill acquisition programming.

Intervention:
The teaching protocol was modified because the prior prompt level was no longer effective for the target program.

Response:
The client participated appropriately and responded well to the updated teaching steps.

Plan:
Continue with the updated teaching procedure and review data next session.

Provider Signature: {provider_name}, BCBA
"""
    if category == "aba_97156_missing_uptake":
        return f"""{SYNTHETIC_NOTICE}

Service Code: 97156
Date of Service: {dos.isoformat()}
Provider: {provider_name}, BCBA
Client: {patient_id}
Duration: 30 minutes
Billed Units: 2

Caregiver:
Caregiver was present for the training visit.

Training Content:
The provider reviewed visual schedule setup and transition prompting steps with the caregiver.

Response:
Caregiver listened to the explanation and asked questions about home routines.

Plan:
Continue caregiver training aligned to transition goals in the treatment plan.

Provider Signature: {provider_name}, BCBA
"""
    if category == "hospice_vague_prognosis":
        return f"""{SYNTHETIC_NOTICE}

Note Type: Hospice Eligibility Review
Date of Service: {dos.isoformat()}
Provider: {provider_name}, RN
Patient: {patient_id}

Face-to-Face:
Face-to-face encounter was reviewed for this synthetic eligibility note.

Summary:
Patient remains appropriate for hospice services. Patient is weak and needs support with daily activities.

Nursing Visit:
Patient was resting in bed. Family reports patient is tired. No new measurements were documented.

Plan of Care:
Continue current plan.

Electronically signed by {provider_name}, RN
"""
    if category == "hospice_poc_mismatch":
        return f"""{SYNTHETIC_NOTICE}

Note Type: Hospice Nursing Note
Date of Service: {dos.isoformat()}
Provider: {provider_name}, RN
Patient: {patient_id}

Face-to-Face:
Not applicable for this synthetic nursing visit.

Summary:
The plan of care emphasizes dyspnea monitoring and caregiver education for medication comfort kit use.

Nursing Visit:
The visit focused only on supply inventory and did not address dyspnea monitoring or caregiver education.

Plan of Care:
Continue current plan without updates.

Electronically signed by {provider_name}, RN
"""
    if category == "bh_weak_mednec":
        return f"""{SYNTHETIC_NOTICE}

Note Type: Behavioral Health Progress Note
Date of Service: {dos.isoformat()}
Provider: {provider_name}, LCSW
Client: {patient_id}

Session Focus:
The session included supportive discussion and review of the weekly schedule.

Intervention:
The provider used general reflection and encouraged journaling.

Risk and Symptom Update:
No acute safety concern was reported in this synthetic note.

Plan:
Continue supportive sessions.

Provider Signature: {provider_name}, LCSW
"""
    if category == "adversarial_invalid_evidence":
        return f"""{SYNTHETIC_NOTICE}

Service Code: 97155
Date of Service: {dos.isoformat()}
Provider: {provider_name}, BCBA
Client: {patient_id}
Duration: 45 minutes
Billed Units: 3

Session Summary:
The provider reviewed acquisition data and observed technician implementation.

Intervention:
Protocol was adjusted during the session.

Response:
The client completed practice activities with variable prompting.

Plan:
Review the protocol again during the next synthetic session.

Provider Signature: {provider_name}, BCBA
"""
    raise ValueError(f"Unknown scenario category: {category}")


def _expected_findings(scenario: Scenario) -> list[dict]:
    if scenario.primary_issue is None:
        return [
            {
                "question_key": "protocol_change_rationale",
                "expected_status": "pass",
                "severity": "critical",
                "must_have_evidence": True,
            },
            {
                "question_key": "individualized_observation",
                "expected_status": "pass",
                "severity": "warning",
                "must_have_evidence": True,
            },
        ]

    severity = "critical"
    if scenario.primary_issue in {"individualized_observation", "caregiver_skill_uptake", "plan_of_care_alignment"}:
        severity = "warning"
    return [
        {
            "question_key": scenario.primary_issue,
            "expected_status": scenario.expected_status,
            "severity": severity,
            "must_have_evidence": scenario.primary_issue not in {"duration_unit_mismatch"},
        }
    ]


def _chunk_document(document: SyntheticDocument) -> DocumentChunk:
    return DocumentChunk(
        document=document,
        chunk_index=0,
        start_char=0,
        end_char=len(document.body),
        text=document.body,
    )


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_database(db: Session, reset: bool = True) -> dict[str, int]:
    if reset:
        reset_database()

    providers_by_external_id: dict[str, Provider] = {}
    for external_id, name, specialty, state in PROVIDERS:
        provider = Provider(
            external_provider_id=external_id,
            name=name,
            specialty=specialty,
            state=state,
        )
        db.add(provider)
        providers_by_external_id[external_id] = provider
    db.flush()

    versions_by_key: dict[tuple[str, str], QuestionSetVersion] = {}
    for question_set_def in QUESTION_SET_DEFS:
        question_set = QuestionSet(
            slug=question_set_def["slug"],
            name=question_set_def["name"],
            specialty=question_set_def["specialty"],
            description=question_set_def["description"],
        )
        db.add(question_set)
        db.flush()
        for version_name, status, change_summary in question_set_def["versions"]:
            version = QuestionSetVersion(
                question_set=question_set,
                version=version_name,
                status=status,
                change_summary=change_summary,
                active_from=date(2026, 1, 1),
            )
            db.add(version)
            versions_by_key[(question_set.slug, version_name)] = version
    db.flush()

    question_count = 0
    for version_key, question_defs in QUESTION_DEFS.items():
        version = versions_by_key[version_key]
        for question_key, criterion_text, severity, check_type, requires_evidence, deterministic_rule, prompt_hint in question_defs:
            db.add(
                Question(
                    version=version,
                    question_key=question_key,
                    criterion_text=criterion_text,
                    severity=severity,
                    check_type=check_type,
                    requires_evidence=requires_evidence,
                    expected_answer_type="pass_fail",
                    deterministic_rule=deterministic_rule,
                    prompt_hint=prompt_hint,
                )
            )
            question_count += 1

    start_date = date(2026, 5, 10)
    document_count = 0
    eval_count = 0
    for scenario in SCENARIOS:
        provider = providers_by_external_id[scenario.provider_external_id]
        version = versions_by_key[(scenario.question_set_slug, scenario.version)]
        for item_index in range(1, scenario.count + 1):
            document_count += 1
            dos = start_date + timedelta(days=document_count % 20)
            patient_id = f"SYN-{scenario.category.upper().replace('_', '-')}-{item_index:03d}"
            body = _note_body(scenario.category, provider.name, patient_id, dos, item_index)
            document = SyntheticDocument(
                provider=provider,
                synthetic_patient_id=patient_id,
                title=f"{scenario.title} {item_index:03d}",
                specialty=provider.specialty,
                service_code=scenario.service_code,
                payer="Synthetic Medicaid MCO" if provider.specialty == "aba" else "Synthetic Payer",
                state=provider.state,
                date_of_service=dos,
                note_type=scenario.note_type,
                body=body,
                source_kind="seeded",
            )
            db.add(document)
            db.flush()
            db.add(_chunk_document(document))
            db.add(
                EvalCase(
                    case_key=f"{scenario.category}_{item_index:03d}",
                    document=document,
                    question_set_version=version,
                    expected_findings=_expected_findings(scenario),
                    tags={
                        "specialty": provider.specialty,
                        "service_code": scenario.service_code,
                        "category": scenario.category,
                        "scenario_type": scenario.category,
                        "question_set": f"{scenario.question_set_slug}-{scenario.version}",
                        "synthetic_only": True,
                    },
                )
            )
            eval_count += 1

    db.add(
        AuditLog(
            actor="system",
            action="seed.reset",
            entity_type="database",
            entity_id=None,
            metadata_json={
                "synthetic_only": True,
                "provider_count": len(PROVIDERS),
                "question_set_version_count": len(versions_by_key),
                "question_count": question_count,
                "document_count": document_count,
                "eval_case_count": eval_count,
            },
        )
    )
    db.commit()

    return {
        "providers": len(PROVIDERS),
        "question_sets": len(QUESTION_SET_DEFS),
        "question_set_versions": len(versions_by_key),
        "questions": question_count,
        "synthetic_documents": document_count,
        "document_chunks": document_count,
        "eval_cases": eval_count,
    }


def main() -> None:
    with SessionLocal() as db:
        counts = seed_database(db)

    print(f"Seeded {counts['providers']} providers")
    print(f"Seeded {counts['question_sets']} question sets")
    print(f"Seeded {counts['question_set_versions']} question set versions")
    print(f"Seeded {counts['questions']} questions")
    print(f"Seeded {counts['synthetic_documents']} synthetic documents")
    print(f"Seeded {counts['document_chunks']} document chunks")
    print(f"Seeded {counts['eval_cases']} eval cases")


if __name__ == "__main__":
    main()
