from .base import RuleResult

def rule_dormant_activation(months_dormant: int, sudden_amount: float):
    if months_dormant >= 10 and sudden_amount >= 50_00_000:
        return RuleResult(
            "DORMANT_GSTIN_ACTIVATION",
            85,
            {"months_dormant": months_dormant, "amount": sudden_amount}
        )
    return RuleResult("NORMAL_ACTIVITY", 0, {})


def rule_burst_invoicing(invoice_count: int, days: int):
    if invoice_count >= 10 and days <= 2:
        return RuleResult(
            "INVOICE_BURST",
            70,
            {"invoice_count": invoice_count, "days": days}
        )
    return RuleResult("NO_BURST", 0, {})
