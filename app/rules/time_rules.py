from datetime import datetime
from .base import RuleResult

def rule_fast_cycle(dates: list):
    """
    dates: list of datetime objects
    """
    if not dates or len(dates) < 2:
        return RuleResult("TIME_INSUFFICIENT_DATA", 0, {})

    days = (max(dates) - min(dates)).days

    if days <= 3:
        return RuleResult("FAST_LOOP_<=3_DAYS", 90, {"duration_days": days})
    elif days <= 7:
        return RuleResult("FAST_LOOP_<=7_DAYS", 70, {"duration_days": days})
    elif days <= 30:
        return RuleResult("FAST_LOOP_<=30_DAYS", 40, {"duration_days": days})
    else:
        return RuleResult("SLOW_LOOP", 0, {"duration_days": days})


def rule_same_day_loop(dates: list):
    unique_days = set(d.date() for d in dates)
    if len(unique_days) == 1:
        return RuleResult("SAME_DAY_LOOP", 95, {"date": str(unique_days.pop())})
    return RuleResult("NOT_SAME_DAY", 0, {})
