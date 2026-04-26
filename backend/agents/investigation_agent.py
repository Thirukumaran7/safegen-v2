"""
SafeGen AI — Autonomous Threat Investigation Agent
Triggered only for borderline inputs where the composite score
falls between allow_max and (allow_max * 1.8).
Runs four autonomous checks and either escalates or downgrades
the decision based on findings.
This is what makes the pipeline genuinely agentic — the flow
is not fixed. It depends on what each check finds.
"""

import re
from agents.rag_engine import retrieve_context


# Soft injection keywords — not strong enough to trigger the 30-pattern
# injection detector but worth flagging in borderline cases
SOFT_INJECTION_KEYWORDS = [
    "ignore", "forget", "pretend", "unrestricted", "override",
    "developer mode", "disable", "bypass", "as if you have no",
    "act as", "roleplay", "simulate", "hypothetically",
    "for testing", "test environment", "academic purposes only",
]

# Malware-proximate keywords — related to malware topics without
# being direct enough to trigger the malware detector
MALWARE_PROXIMITY_KEYWORDS = [
    "encrypt", "decrypt", "payload", "shell", "execute",
    "privilege", "escalate privileges", "root access",
    "kernel", "inject", "exfiltrate", "lateral movement",
    "persistence", "obfuscate", "reverse engineering",
]

# Minimum RAG score to consider a match strong enough for downgrade
RAG_DOWNGRADE_THRESHOLD = 3.0

# Minimum number of soft injection keywords to trigger escalation
SOFT_INJECTION_MIN = 1

# Minimum number of proximity keywords to trigger escalation
PROXIMITY_MIN = 2


def investigate(
    analysis:  dict,
    policy:    str,
    role:      str,
    db,
) -> dict:
    """
    Run autonomous investigation for borderline inputs.

    Args:
        analysis: Full analysis result from risk_analyzer
        policy:   Active policy level
        role:     Active user role
        db:       SQLAlchemy database session

    Returns:
        dict with keys:
            investigated:       bool — whether investigation ran
            original_decision:  str  — decision before investigation
            final_decision:     str  — decision after investigation
            findings:           list — what each check found
            escalated:          bool
            downgraded:         bool
            reason:             str
            checks_run:         list — which checks were evaluated
    """

    score      = analysis["scoring"]["final_score"]
    thresholds = analysis["decision"]["thresholds_used"]
    allow_max  = thresholds["allow_max"]
    original   = analysis["decision"]["decision"]

    # Only investigate borderline cases
    is_borderline = allow_max <= score <= allow_max * 1.8

    if not is_borderline:
        return {
            "investigated":      False,
            "original_decision": original,
            "final_decision":    original,
            "findings":          [],
            "escalated":         False,
            "downgraded":        False,
            "reason":            "Score outside borderline range — no investigation needed",
            "checks_run":        [],
        }

    findings   = []
    escalate   = False
    downgrade  = False
    checks_run = []
    text       = analysis.get("original_text", "").lower()

    # ── Check 1 — Session history pattern ────────────────────────
    checks_run.append("session_history")
    try:
        from database.models import AnalysisLog
        from sqlalchemy import desc

        recent = (
            db.query(AnalysisLog)
            .filter(AnalysisLog.role == role)
            .order_by(desc(AnalysisLog.timestamp))
            .limit(10)
            .all()
        )

        recent_suspicious = [
            r for r in recent
            if r.intent_label in ("suspicious", "malicious")
            or r.final_score > 3.5
        ]

        if len(recent_suspicious) >= 3:
            escalate = True
            findings.append(
                f"Session history: {len(recent_suspicious)} suspicious or high-scoring "
                f"queries detected in recent history for role '{role}' — possible probing"
            )
        else:
            findings.append(
                f"Session history: {len(recent_suspicious)} suspicious queries in recent "
                f"history — below escalation threshold"
            )
    except Exception as e:
        findings.append(f"Session history check failed: {str(e)}")

    # ── Check 2 — Soft injection keyword proximity ────────────────
    checks_run.append("soft_injection")
    soft_matches = [kw for kw in SOFT_INJECTION_KEYWORDS if kw in text]

    if len(soft_matches) >= SOFT_INJECTION_MIN:
        escalate = True
        findings.append(
            f"Soft injection proximity: {len(soft_matches)} soft injection keyword(s) "
            f"detected — {soft_matches[:3]}"
        )
    else:
        findings.append("Soft injection proximity: no soft injection keywords detected")

    # ── Check 3 — RAG legitimacy check ───────────────────────────
    checks_run.append("rag_legitimacy")
    try:
        rag_result = retrieve_context(analysis.get("original_text", ""), top_k=1)

        if rag_result["sources"] and rag_result["sources"][0]["score"] >= RAG_DOWNGRADE_THRESHOLD:
            top_doc   = rag_result["sources"][0]
            downgrade = True
            findings.append(
                f"RAG legitimacy: strong knowledge base match found — "
                f"'{top_doc['title']}' (BM25: {top_doc['score']}) — "
                f"query is likely a legitimate institutional request"
            )
        else:
            score_str = (
                f"{rag_result['sources'][0]['score']:.2f}"
                if rag_result["sources"]
                else "no match"
            )
            findings.append(
                f"RAG legitimacy: no strong knowledge base match — "
                f"top score {score_str} (threshold {RAG_DOWNGRADE_THRESHOLD})"
            )
    except Exception as e:
        findings.append(f"RAG legitimacy check failed: {str(e)}")

    # ── Check 4 — Malware keyword proximity ──────────────────────
    checks_run.append("malware_proximity")
    proximity_matches = [kw for kw in MALWARE_PROXIMITY_KEYWORDS if kw in text]

    if len(proximity_matches) >= PROXIMITY_MIN:
        escalate = True
        findings.append(
            f"Malware proximity: {len(proximity_matches)} malware-adjacent keyword(s) "
            f"detected — {proximity_matches[:3]} — escalating borderline to BLOCK"
        )
    else:
        findings.append(
            f"Malware proximity: {len(proximity_matches)} malware-adjacent keyword(s) — "
            f"below escalation threshold of {PROXIMITY_MIN}"
        )

    # ── Final decision ────────────────────────────────────────────
    # Escalation takes priority over downgrade
    if escalate:
        final_decision = "BLOCK"
        reason = (
            f"Investigation agent escalated from {original} to BLOCK — "
            f"findings: {'; '.join([f for f in findings if any(kw in f.lower() for kw in ['detected', 'match', 'suspicious', 'found'])])}"
        )
    elif downgrade and not escalate:
        final_decision = "ALLOW"
        reason = (
            f"Investigation agent downgraded from {original} to ALLOW — "
            f"strong knowledge base match indicates legitimate institutional query"
        )
    else:
        final_decision = original
        reason = (
            f"Investigation agent ran {len(checks_run)} checks — "
            f"no escalation or downgrade signals found — maintaining {original}"
        )

    return {
        "investigated":      True,
        "original_decision": original,
        "final_decision":    final_decision,
        "findings":          findings,
        "escalated":         escalate,
        "downgraded":        downgrade,
        "reason":            reason,
        "checks_run":        checks_run,
    }


def format_investigation_result(inv_result: dict) -> dict:
    """
    Format investigation result for inclusion in the API response.
    """
    return {
        "investigation_run":      inv_result["investigated"],
        "investigation_findings": inv_result["findings"],
        "investigation_escalated": inv_result.get("escalated", False),
        "investigation_downgraded": inv_result.get("downgraded", False),
        "investigation_reason":   inv_result.get("reason"),
        "checks_run":             inv_result.get("checks_run", []),
    }