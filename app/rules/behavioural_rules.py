from .base import RuleResult

def rule_dormant_activation(months_dormant: int, sudden_amount: float):
    if months_dormant >= 6 and sudden_amount >= 5_000_00:
        return RuleResult(
            "DORMANT_GSTIN_ACTIVATION",
            85,
            {"months_dormant": months_dormant, "amount": sudden_amount}
        )
    return RuleResult("NORMAL_ACTIVITY", 0, {})


def rule_burst_invoicing(invoice_count: int, days_window: int):
    if invoice_count >= 5 and days_window <= 5:
        return RuleResult(
            "INVOICE_BURST",
            70,
            {"invoice_count": invoice_count, "days_window": days_window}
        )
    return RuleResult("NO_BURST", 0, {})
