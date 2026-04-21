"""
SafeGen AI — Decision Engine
Four decisions: ALLOW / RESTRICT / REDACT / BLOCK
REDACT — reserved exclusively for PII detection (only when no malware present)
BLOCK  — score based OR injection detected OR malware with high score
"""

from .policy import get_thresholds

DECISION_DESCRIPTIONS = {
    "ALLOW":    "Input is safe. Full response provided.",
    "RESTRICT": "Input is borderline. High-level response only. No technical details.",
    "REDACT":   "Sensitive data detected and masked. Partial response provided.",
    "BLOCK":    "Input violates safety policy. Request denied.",
}


def make_decision(
    final_score:          float,
    policy:               str,
    role:                 str,
    sensitive_data_found: bool = False,
    injection_detected:   bool = False,
    malware_detected:     bool = False,
) -> dict:

    # Injection → immediate BLOCK regardless of score
    if injection_detected:
        return {
            "decision":        "BLOCK",
            "reason":          "Prompt injection attempt detected — request blocked",
            "description":     DECISION_DESCRIPTIONS["BLOCK"],
            "thresholds_used": get_thresholds(policy, role),
            "override":        "injection_detected",
        }

    thresholds = get_thresholds(policy, role)

    # Score-based decision
    if final_score < thresholds["allow_max"]:
        decision = "ALLOW"
        reason   = f"Score {final_score} is within safe threshold of {thresholds['allow_max']}"
    elif final_score < thresholds["restrict_max"]:
        decision = "RESTRICT"
        reason   = f"Score {final_score} exceeds allow threshold of {thresholds['allow_max']}"
    elif final_score < thresholds["block_max"]:
        decision = "RESTRICT"
        reason   = f"Score {final_score} exceeds restrict threshold of {thresholds['restrict_max']} — elevated restriction applied"
    else:
        decision = "BLOCK"
        reason   = f"Score {final_score} exceeds block threshold of {thresholds['block_max']}"

    # PII override — REDACT only when:
    # 1. Sensitive data was found
    # 2. Score-based decision was ALLOW or RESTRICT
    # 3. No malware detected (malware cases should stay RESTRICT or BLOCK, not be downgraded to REDACT)
    if sensitive_data_found and decision in ("ALLOW", "RESTRICT") and not malware_detected:
        decision = "REDACT"
        reason   = "Sensitive data detected in input — content masked"

    return {
        "decision":        decision,
        "reason":          reason,
        "description":     DECISION_DESCRIPTIONS[decision],
        "thresholds_used": thresholds,
        "override":        None,
    }