"""
SafeGen AI — Policy Engine (Extended with Ticket Roles)
12 configurations: 6 roles × 3 policies
New roles: customer, agent, admin for enterprise ticketing
"""

POLICY_THRESHOLDS = {
    "strict": {
        "student":  {"allow_max": 1.5, "restrict_max": 3.0, "block_max": 5.0},
        "general":  {"allow_max": 2.0, "restrict_max": 3.5, "block_max": 5.5},
        "expert":   {"allow_max": 2.5, "restrict_max": 4.5, "block_max": 7.0},
        "customer": {"allow_max": 1.5, "restrict_max": 3.0, "block_max": 5.0},
        "agent":    {"allow_max": 2.5, "restrict_max": 4.5, "block_max": 7.0},
        "admin":    {"allow_max": 4.0, "restrict_max": 6.0, "block_max": 8.5},
    },
    "moderate": {
        "student":  {"allow_max": 2.0, "restrict_max": 4.0, "block_max": 6.5},
        "general":  {"allow_max": 2.5, "restrict_max": 4.5, "block_max": 7.0},
        "expert":   {"allow_max": 3.5, "restrict_max": 6.0, "block_max": 8.0},
        "customer": {"allow_max": 1.5, "restrict_max": 4.0, "block_max": 6.0},
        "agent":    {"allow_max": 3.5, "restrict_max": 5.5, "block_max": 7.5},
        "admin":    {"allow_max": 5.0, "restrict_max": 7.0, "block_max": 9.0},
    },
    "open": {
        "student":  {"allow_max": 3.0, "restrict_max": 5.5, "block_max": 7.5},
        "general":  {"allow_max": 4.0, "restrict_max": 6.0, "block_max": 8.0},
        "expert":   {"allow_max": 5.0, "restrict_max": 7.5, "block_max": 9.0},
        "customer": {"allow_max": 2.5, "restrict_max": 5.0, "block_max": 7.0},
        "agent":    {"allow_max": 4.5, "restrict_max": 6.5, "block_max": 8.5},
        "admin":    {"allow_max": 6.0, "restrict_max": 8.0, "block_max": 9.5},
    },
}


def get_thresholds(policy: str, role: str) -> dict:
    policy_config = POLICY_THRESHOLDS.get(policy, POLICY_THRESHOLDS["moderate"])
    return policy_config.get(role, policy_config["general"])