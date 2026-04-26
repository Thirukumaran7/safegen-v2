"""
SafeGen AI — Multi-Turn Conversation Agent
Detects attack patterns that span multiple conversation turns.
A single suspicious query might score low and pass through.
But three borderline queries in sequence on the same topic
is a different risk profile entirely.
"""

from datetime import datetime, timezone


# Label sequences that indicate escalating attack patterns
ESCALATION_SEQUENCES = [
    ["benign", "suspicious", "malicious"],
    ["benign", "benign", "malicious"],
    ["suspicious", "suspicious", "suspicious"],
    ["benign", "suspicious", "suspicious"],
]

# Topic clusters — if queries share a topic AND labels escalate, it is suspicious
TOPIC_CLUSTERS = {
    "access_control": [
        "admin", "root", "privilege", "override", "bypass",
        "access", "login", "password", "credentials", "authentication"
    ],
    "data_extraction": [
        "list", "all", "export", "dump", "extract", "download",
        "database", "records", "emails", "phone", "customer", "student"
    ],
    "malware_related": [
        "encrypt", "ransomware", "payload", "execute", "shell",
        "inject", "exploit", "vulnerability", "keylogger", "backdoor"
    ],
    "injection_related": [
        "ignore", "pretend", "forget", "unrestricted", "jailbreak",
        "override", "disable", "bypass", "developer", "mode"
    ],
}

# Minimum number of suspicious/malicious in recent history to trigger escalation
SUSPICIOUS_THRESHOLD = 3


def analyse_conversation(history: list, current_text: str) -> dict:
    """
    Analyse the conversation history alongside the current input.
    Returns escalation signal with reason and override score if detected.

    Args:
        history: List of previous analysis results from the session.
                 Each entry should have: intent_label, final_score, text, decision
        current_text: The current input being analysed

    Returns:
        dict with keys:
            escalation_detected: bool
            reason: str or None
            override_score: float or None (used to override composite score)
            pattern_found: list or None
            checks_run: list of check names that were evaluated
    """

    checks_run = []

    # Not enough history to detect patterns
    if not history or len(history) < 2:
        return {
            "escalation_detected": False,
            "reason":              None,
            "override_score":      None,
            "pattern_found":       None,
            "checks_run":          ["insufficient_history"],
        }

    # ── Check 1 — Label escalation sequence ──────────────────────
    checks_run.append("label_escalation")
    recent_labels = [h.get("intent_label", "benign") for h in history[-3:]]

    for seq in ESCALATION_SEQUENCES:
        if len(recent_labels) >= len(seq) - 1:
            window = recent_labels[-(len(seq) - 1):]
            if window == seq[:-1]:
                # Current query completes the escalation pattern
                if _shares_topic(history[-2:], current_text):
                    return {
                        "escalation_detected": True,
                        "reason":              f"Escalating label pattern detected across {len(seq)} turns: {seq[:-1]} → [current]",
                        "override_score":      7.5,
                        "pattern_found":       window,
                        "checks_run":          checks_run,
                    }

    # ── Check 2 — Rapid suspicious queries (volume-based) ─────────
    checks_run.append("volume_check")
    recent_suspicious = [
        h for h in history[-6:]
        if h.get("intent_label") in ("suspicious", "malicious")
        or h.get("final_score", 0) > 3.0
    ]

    if len(recent_suspicious) >= SUSPICIOUS_THRESHOLD:
        return {
            "escalation_detected": True,
            "reason":              f"{len(recent_suspicious)} suspicious or high-scoring queries detected in recent session — possible probing attack",
            "override_score":      8.0,
            "pattern_found":       [h.get("intent_label") for h in recent_suspicious],
            "checks_run":          checks_run,
        }

    # ── Check 3 — Topic drift toward sensitive cluster ────────────
    checks_run.append("topic_drift")
    all_text = " ".join(
        [h.get("text", "") for h in history[-4:]] + [current_text]
    ).lower()

    for cluster_name, keywords in TOPIC_CLUSTERS.items():
        matched_keywords = [kw for kw in keywords if kw in all_text]
        if len(matched_keywords) >= 4:
            # Four or more keywords from the same cluster across recent turns
            recent_decisions = [h.get("decision", "ALLOW") for h in history[-3:]]
            if "RESTRICT" in recent_decisions or "BLOCK" in recent_decisions:
                return {
                    "escalation_detected": True,
                    "reason":              f"Topic drift toward '{cluster_name}' cluster detected across {len(history[-4:])+1} turns — keywords: {matched_keywords[:4]}",
                    "override_score":      6.5,
                    "pattern_found":       matched_keywords[:4],
                    "checks_run":          checks_run,
                }

    # ── Check 4 — Repeated near-identical queries ─────────────────
    checks_run.append("repetition_check")
    current_words = set(current_text.lower().split())

    for prev in history[-5:]:
        prev_text  = prev.get("text", "")
        prev_words = set(prev_text.lower().split())
        if len(current_words) > 3 and len(prev_words) > 3:
            overlap = len(current_words & prev_words) / max(len(current_words), len(prev_words))
            if overlap > 0.7 and prev.get("decision") in ("RESTRICT", "BLOCK"):
                return {
                    "escalation_detected": True,
                    "reason":              f"Repeated query detected (70%+ word overlap with a previously restricted/blocked query) — possible evasion attempt",
                    "override_score":      7.0,
                    "pattern_found":       list(current_words & prev_words)[:5],
                    "checks_run":          checks_run,
                }

    # No escalation detected
    return {
        "escalation_detected": False,
        "reason":              None,
        "override_score":      None,
        "pattern_found":       None,
        "checks_run":          checks_run,
    }


def _shares_topic(recent_history: list, current_text: str) -> bool:
    """
    Check if the current query shares a topic cluster with recent history.
    Used to confirm that a label escalation is on-topic rather than coincidental.
    """
    combined = " ".join(
        [h.get("text", "") for h in recent_history] + [current_text]
    ).lower()

    for cluster_name, keywords in TOPIC_CLUSTERS.items():
        matched = sum(1 for kw in keywords if kw in combined)
        if matched >= 2:
            return True

    return False


def format_multiturn_result(mt_result: dict) -> dict:
    """
    Format the multi-turn result for inclusion in the API response.
    """
    return {
        "multiturn_check":        True,
        "escalation_detected":    mt_result["escalation_detected"],
        "multiturn_reason":       mt_result.get("reason"),
        "multiturn_override":     mt_result.get("override_score"),
        "multiturn_pattern":      mt_result.get("pattern_found"),
        "multiturn_checks_run":   mt_result.get("checks_run", []),
    }