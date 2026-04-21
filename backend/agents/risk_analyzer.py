"""
SafeGen AI v2 — Risk Analyzer Agent
Agent 1: Runs three detectors in parallel and computes final risk score
Includes RAG security checkpoint
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors.malware_detector import detect_malware
from detectors.sensitive_data_detector import detect_sensitive_data
from detectors.intent_classifier import classify_intent
from engine.scoring import compute_final_score
from engine.decision import make_decision


def run_risk_analysis(
    text:    str,
    policy:  str = "moderate",
    role:    str = "general",
    use_rag: bool = True,
) -> dict:

    # Step 1 — Run all three detectors
    malware_result   = detect_malware(text)
    sensitive_result = detect_sensitive_data(text)
    intent_result    = classify_intent(text)

    # Step 2 — Compute weighted score
    scoring_result = compute_final_score(
        malware_score   = malware_result["score"],
        sensitive_score = sensitive_result["score"],
        intent_score    = intent_result["score"],
        role            = role,
    )

    # Step 3 — Make decision
    decision_result = make_decision(
    final_score          = scoring_result["final_score"],
    policy               = policy,
    role                 = role,
    sensitive_data_found = sensitive_result["contains_sensitive"],
    injection_detected   = intent_result["injection_detected"],
    malware_detected     = malware_result["malware_type"] != "None",  # add this
)

    # Step 4 — RAG retrieval (only if decision is ALLOW or RESTRICT)
    rag_context = ""
    rag_sources = []
    rag_used    = False

    if use_rag and decision_result["decision"] == "ALLOW":
        try:
            from agents.rag_engine import retrieve_context
            rag_result  = retrieve_context(text)
            rag_context = rag_result.get("context", "")
            rag_sources = rag_result.get("sources", [])
            rag_used    = len(rag_sources) > 0
        except Exception as e:
            print(f"RAG retrieval skipped: {e}")

    # Step 5 — Build explanation
    explanation = []

    if malware_result["flags"]:
        explanation.append(f"Malware indicators detected: {', '.join(malware_result['flags'][:3])}")
        explanation.append(f"Threat type: {malware_result['malware_type']} — {malware_result['description']}")
    else:
        explanation.append("No malware indicators detected")

    if sensitive_result["types_found"]:
        explanation.append(f"Privacy: {sensitive_result['pii_summary']}")
        explanation.append(f"Anonymisation score: {sensitive_result['anonymisation_score']}% — Risk: {sensitive_result['privacy_risk']}")
    else:
        explanation.append("No sensitive data detected")

    explanation.append(f"Intent: {intent_result['threat_category']} (confidence: {round(intent_result['confidence'], 3)})")

    if intent_result["injection_detected"]:
        explanation.append(f"Injection detected: {', '.join(intent_result['injection_patterns'][:2])}")

    explanation.append(
        f"Final score: {scoring_result['final_score']}/10 — "
        f"Malware contributed {scoring_result['contributions']['malware']}, "
        f"Sensitive contributed {scoring_result['contributions']['sensitive']}, "
        f"Intent contributed {scoring_result['contributions']['intent']}"
    )
    explanation.append(f"Decision: {decision_result['decision']} — {decision_result['reason']}")

    if rag_used:
        explanation.append(f"RAG: Retrieved {len(rag_sources)} relevant document(s) from knowledge base")

    # Step 6 — Use masked text if PII found
    display_text = sensitive_result["masked_text"] if sensitive_result["contains_sensitive"] else text

    return {
        "original_text":  text,
        "display_text":   display_text,
        "malware":        malware_result,
        "sensitive":      sensitive_result,
        "intent":         intent_result,
        "scoring":        scoring_result,
        "decision":       decision_result,
        "explanation":    explanation,
        "rag_context":    rag_context,
        "rag_sources":    rag_sources,
        "rag_used":       rag_used,
        "policy":         policy,
        "role":           role,
    }