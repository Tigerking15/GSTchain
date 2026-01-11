def score_cycle(rule_results: list):
    total_score = 0
    reasons = []

    for r in rule_results:
        total_score += r.risk
        if r.risk > 0:
            reasons.append(r.to_dict())

    return {
        "final_risk_score": min(total_score, 100),
        "risk_level": (
            "HIGH" if total_score >= 80 else
            "MEDIUM" if total_score >= 40 else
            "LOW"
        ),
        "reasons": reasons
    }
