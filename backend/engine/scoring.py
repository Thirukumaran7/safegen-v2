"""
SafeGen AI — Scoring Engine
Weighted combination of three detector scores
Intent carries 65-70% weight as primary signal
Ticket roles (customer/agent/admin) have higher malware weights
because data extraction and social engineering are primary threats
in enterprise ticketing contexts
"""

ROLE_WEIGHTS = {
    # ── College helpdesk roles ────────────────────────────────────
    "student": {
        "malware":   0.20,
        "sensitive": 0.15,
        "intent":    0.65,
    },
    "general": {
        "malware":   0.15,
        "sensitive": 0.15,
        "intent":    0.70,
    },
    "expert": {
        "malware":   0.15,
        "sensitive": 0.20,
        "intent":    0.65,
    },
    # ── Enterprise ticketing roles ────────────────────────────────
    # Customer: highest malware weight — data extraction and social
    # engineering are the primary threats from the customer role
    "customer": {
    "malware":   0.33,
    "sensitive": 0.33,
    "intent":    0.34,
},
    # Agent: balanced — needs to handle sensitive data legitimately
    "agent": {
        "malware":   0.20,
        "sensitive": 0.20,
        "intent":    0.60,
    },
    # Admin: intent-primary — admin queries are typically legitimate
    # but still need full pipeline coverage
    "admin": {
        "malware":   0.15,
        "sensitive": 0.20,
        "intent":    0.65,
    },
}


def compute_final_score(
    malware_score:   float,
    sensitive_score: float,
    intent_score:    float,
    role:            str = "general",
) -> dict:
    weights = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS["general"])

    final = (
        weights["malware"]   * malware_score   +
        weights["sensitive"] * sensitive_score +
        weights["intent"]    * intent_score
    )
    final = round(min(10.0, max(0.0, final)), 2)

    return {
        "final_score":  final,
        "weights_used": weights,
        "contributions": {
            "malware":   round(weights["malware"]   * malware_score,   2),
            "sensitive": round(weights["sensitive"] * sensitive_score, 2),
            "intent":    round(weights["intent"]    * intent_score,    2),
        },
    }