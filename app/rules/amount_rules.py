from .base import RuleResult

def rule_amount_similarity(amounts: list):
    if not amounts or len(amounts) < 2:
        return RuleResult("AMOUNT_INSUFFICIENT_DATA", 0, {})

    max_amt = max(amounts)
    min_amt = min(amounts)

    if max_amt == 0:
        return RuleResult("ZERO_AMOUNT", 0, {})

    diff_pct = ((max_amt - min_amt) / max_amt) * 100

    if diff_pct <= 2:
        return RuleResult("ROUND_TRIP_<=2%", 80, {"difference_pct": diff_pct})
    elif diff_pct <= 5:
        return RuleResult("ROUND_TRIP_<=5%", 60, {"difference_pct": diff_pct})
    else:
        return RuleResult("NORMAL_AMOUNT_VARIATION", 0, {"difference_pct": diff_pct})


def rule_exact_amount_repetition(amounts: list):
    if len(amounts) >= 3 and len(set(amounts)) == 1:
        return RuleResult(
            "EXACT_AMOUNT_REPEATED",
            75,
            {"amount": amounts[0]}
        )
    return RuleResult("NO_EXACT_REPETITION", 0, {})


def rule_amount_echo(amounts: list):
    if len(amounts) < 3:
        return RuleResult("INSUFFICIENT_DATA", 0, {})

    rounded = [round(a, -2) for a in amounts]
    if len(set(rounded)) <= 2:
        return RuleResult(
            "AMOUNT_ECHO",
            60,
            {"rounded_amounts": rounded}
        )
    return RuleResult("NO_AMOUNT_ECHO", 0, {})
