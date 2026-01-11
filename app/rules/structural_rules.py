from .base import RuleResult

def rule_small_closed_group(node_count: int):
    if node_count <= 3:
        return RuleResult("TINY_CLOSED_GROUP", 80, {"nodes": node_count})
    elif node_count <= 5:
        return RuleResult("SMALL_CLOSED_GROUP", 50, {"nodes": node_count})
    else:
        return RuleResult("LARGE_NETWORK", 0, {"nodes": node_count})


def rule_layering(path_length: int):
    if path_length >= 6:
        return RuleResult("HEAVY_LAYERING", 60, {"layers": path_length})
    elif path_length >= 4:
        return RuleResult("MODERATE_LAYERING", 30, {"layers": path_length})
    return RuleResult("NO_LAYERING", 0, {"layers": path_length})
