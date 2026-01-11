from typing import Dict

class RuleResult:
    def __init__(self, rule_id: str, risk: int, details: Dict):
        self.rule_id = rule_id
        self.risk = risk              # 0–100
        self.details = details

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "risk": self.risk,
            "details": self.details
        }
