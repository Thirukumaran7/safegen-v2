"""
SafeGen AI — Feedback-Driven Threshold Calibration Module
Analyses user feedback (thumbs up / thumbs down) to identify
miscalibrated thresholds and propose adjustments.
Run this script directly to see recommendations:
    cd backend
    python calibrate_thresholds.py
Or call the /calibrate endpoint in the running API.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import SessionLocal, AnalysisLog, FeedbackLog


# Minimum feedback entries needed before making a recommendation
MIN_FEEDBACK_REQUIRED = 5

# How much to shift the threshold when miscalibration is detected
ADJUSTMENT_STEP = 0.5

# Score bands used to classify false positives and false negatives
# A false positive is a BLOCK or RESTRICT that the user said was wrong
# A false negative is an ALLOW that the user said was wrong
FALSE_POSITIVE_DECISIONS  = ("BLOCK", "RESTRICT", "REDACT")
FALSE_NEGATIVE_DECISIONS  = ("ALLOW",)


def calibrate(db, role: str, policy: str) -> dict:
    """
    Analyse feedback for a specific role and policy combination.
    Returns threshold adjustment recommendations if sufficient data exists.
    """

    # Get all analysis logs for this role and policy that have feedback
    try:
        disagreed_logs = (
            db.query(AnalysisLog)
            .join(FeedbackLog, FeedbackLog.analysis_id == AnalysisLog.id)
            .filter(
                FeedbackLog.agreed    == False,
                AnalysisLog.role      == role,
                AnalysisLog.policy    == policy,
            )
            .all()
        )

        agreed_logs = (
            db.query(AnalysisLog)
            .join(FeedbackLog, FeedbackLog.analysis_id == AnalysisLog.id)
            .filter(
                FeedbackLog.agreed    == True,
                AnalysisLog.role      == role,
                AnalysisLog.policy    == policy,
            )
            .all()
        )

    except Exception as e:
        return {
            "status":  "error",
            "message": f"Database query failed: {str(e)}",
            "role":    role,
            "policy":  policy,
        }

    total_feedback = len(disagreed_logs) + len(agreed_logs)

    if total_feedback < MIN_FEEDBACK_REQUIRED:
        return {
            "status":            "insufficient_data",
            "role":              role,
            "policy":            policy,
            "total_feedback":    total_feedback,
            "minimum_required":  MIN_FEEDBACK_REQUIRED,
            "message":           f"Need at least {MIN_FEEDBACK_REQUIRED} feedback entries. Have {total_feedback}.",
        }

    # Separate false positives and false negatives
    false_positives = [
        log for log in disagreed_logs
        if log.decision in FALSE_POSITIVE_DECISIONS
    ]
    false_negatives = [
        log for log in disagreed_logs
        if log.decision in FALSE_NEGATIVE_DECISIONS
    ]

    agreement_rate = round(
        (len(agreed_logs) / total_feedback * 100) if total_feedback > 0 else 0, 1
    )

    recommendations = {}
    analysis_notes  = []

    # ── False positive analysis ───────────────────────────────────
    # System is blocking/restricting things that should be allowed
    # Recommendation: raise the allow_max threshold
    if false_positives:
        fp_scores = [log.final_score for log in false_positives]
        avg_fp    = round(sum(fp_scores) / len(fp_scores), 2)
        max_fp    = round(max(fp_scores), 2)
        min_fp    = round(min(fp_scores), 2)

        suggested_allow_max = round(avg_fp + ADJUSTMENT_STEP, 1)

        recommendations["allow_max"] = {
            "issue":             "false_positives",
            "count":             len(false_positives),
            "avg_score":         avg_fp,
            "score_range":       f"{min_fp} — {max_fp}",
            "suggested_value":   suggested_allow_max,
            "reason":            (
                f"{len(false_positives)} queries were blocked or restricted "
                f"but users marked them as incorrect decisions. "
                f"Average score of these cases: {avg_fp}. "
                f"Raising allow_max to {suggested_allow_max} would allow "
                f"these borderline legitimate queries through."
            ),
        }
        analysis_notes.append(
            f"False positives: {len(false_positives)} over-restricted queries "
            f"(avg score {avg_fp}) — allow_max may be too low"
        )

    # ── False negative analysis ───────────────────────────────────
    # System is allowing things that should be blocked
    # Recommendation: lower the block_max threshold
    if false_negatives:
        fn_scores = [log.final_score for log in false_negatives]
        avg_fn    = round(sum(fn_scores) / len(fn_scores), 2)
        max_fn    = round(max(fn_scores), 2)
        min_fn    = round(min(fn_scores), 2)

        suggested_block_max = round(avg_fn - ADJUSTMENT_STEP, 1)

        recommendations["block_max"] = {
            "issue":             "false_negatives",
            "count":             len(false_negatives),
            "avg_score":         avg_fn,
            "score_range":       f"{min_fn} — {max_fn}",
            "suggested_value":   suggested_block_max,
            "reason":            (
                f"{len(false_negatives)} queries were allowed "
                f"but users marked them as incorrect decisions. "
                f"Average score of these cases: {avg_fn}. "
                f"Lowering block_max to {suggested_block_max} would "
                f"catch these under-detected harmful queries."
            ),
        }
        analysis_notes.append(
            f"False negatives: {len(false_negatives)} under-detected queries "
            f"(avg score {avg_fn}) — block_max may be too high"
        )

    # ── Well calibrated ───────────────────────────────────────────
    if not false_positives and not false_negatives:
        analysis_notes.append(
            "No systematic miscalibration detected — "
            "thresholds appear well calibrated for this role and policy"
        )

    return {
        "status":           "recommendations_available" if recommendations else "well_calibrated",
        "role":             role,
        "policy":           policy,
        "total_feedback":   total_feedback,
        "agreed":           len(agreed_logs),
        "disagreed":        len(disagreed_logs),
        "agreement_rate":   agreement_rate,
        "false_positives":  len(false_positives),
        "false_negatives":  len(false_negatives),
        "analysis_notes":   analysis_notes,
        "recommendations":  recommendations,
    }


def calibrate_all(db) -> dict:
    """
    Run calibration across all role and policy combinations.
    Returns only combinations with sufficient data and recommendations.
    """
    roles    = ["student", "general", "expert", "customer", "agent", "admin"]
    policies = ["strict", "moderate", "open"]
    results  = {}

    for role in roles:
        for policy in policies:
            result = calibrate(db, role, policy)
            if result["status"] in ("recommendations_available", "well_calibrated"):
                results[f"{role}_{policy}"] = result

    return {
        "configurations_analysed": len(roles) * len(policies),
        "configurations_with_data": len(results),
        "results": results,
    }


def print_report(results: dict):
    """
    Print a human-readable calibration report to the terminal.
    """
    print("\n" + "="*60)
    print("SAFEGEN AI — THRESHOLD CALIBRATION REPORT")
    print("="*60)

    if "results" in results:
        # Full report from calibrate_all
        print(f"Configurations analysed:   {results['configurations_analysed']}")
        print(f"Configurations with data:  {results['configurations_with_data']}")
        print()
        for key, result in results["results"].items():
            _print_single(result)
    else:
        # Single configuration result
        _print_single(results)

    print("="*60 + "\n")


def _print_single(result: dict):
    print(f"\nRole: {result.get('role','?')} | Policy: {result.get('policy','?')}")
    print(f"  Status: {result['status']}")

    if result['status'] == 'insufficient_data':
        print(f"  Feedback collected: {result.get('total_feedback', 0)} "
              f"(need {result.get('minimum_required', 5)})")
        print(f"  Message: {result.get('message', '')}")
        return

    if result['status'] == 'error':
        print(f"  Error: {result.get('message', 'unknown error')}")
        return

    print(f"  Feedback: {result.get('total_feedback', 0)} total | "
          f"{result.get('agreed', 0)} agreed | "
          f"{result.get('disagreed', 0)} disagreed | "
          f"Agreement rate: {result.get('agreement_rate', 0)}%")

    for note in result.get("analysis_notes", []):
        print(f"  Note: {note}")

    for threshold, rec in result.get("recommendations", {}).items():
        print(f"\n  Recommendation — {threshold}:")
        print(f"    Issue:           {rec['issue']}")
        print(f"    Count:           {rec['count']} cases")
        print(f"    Score range:     {rec['score_range']}")
        print(f"    Suggested value: {rec['suggested_value']}")
        print(f"    Reason:          {rec['reason']}")


# ── Run directly ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running threshold calibration analysis...")
    db = SessionLocal()
    try:
        if len(sys.argv) == 3:
            # Run for specific role and policy
            role   = sys.argv[1]
            policy = sys.argv[2]
            print(f"Analysing: {role} + {policy}")
            result = calibrate(db, role, policy)
            print_report(result)
        else:
            # Run for all combinations
            result = calibrate_all(db)
            print_report(result)
    finally:
        db.close()