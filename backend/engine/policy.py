"""
SafeGen AI v2 — Policy Engine
9 configurations: 3 roles x 3 policies
Each config has independent allow/restrict/block thresholds
"""

POLICY_THRESHOLDS = {
    "strict": {
        "student": {
            "allow_max":    1.5,
            "restrict_max": 3.0,
            "block_max":    5.0,
        },
        "general": {
            "allow_max":    2.0,
            "restrict_max": 3.5,
            "block_max":    5.5,
        },
        "expert": {
            "allow_max":    2.5,
            "restrict_max": 4.5,
            "block_max":    7.0,
        },
    },
    "moderate": {
        "student": {
            "allow_max":    2.0,
            "restrict_max": 4.0,
            "block_max":    6.5,
        },
        "general": {
            "allow_max":    2.5,
            "restrict_max": 4.5,
            "block_max":    7.0,
        },
        "expert": {
            "allow_max":    3.5,
            "restrict_max": 6.0,
            "block_max":    8.0,
        },
    },
    "open": {
        "student": {
            "allow_max":    3.0,
            "restrict_max": 5.5,
            "block_max":    7.5,
        },
        "general": {
            "allow_max":    4.0,
            "restrict_max": 6.0,
            "block_max":    8.0,
        },
        "expert": {
            "allow_max":    5.0,
            "restrict_max": 7.5,
            "block_max":    9.0,
        },
    },
}


def get_thresholds(policy: str, role: str) -> dict:
    policy_config = POLICY_THRESHOLDS.get(policy, POLICY_THRESHOLDS["moderate"])
    return policy_config.get(role, policy_config["general"])