# rules/pan_rules.py
from .base import RuleResult

def rule_pan_cluster(pan: str, gstins: list, threshold=3):
    if len(set(gstins)) >= threshold:
        return RuleResult(
            "PAN_CLUSTER",
            50,
            {"pan": pan, "gstins": gstins}
        )
    return RuleResult("NO_PAN_CLUSTER", 0, {})
