# scripts/check_cycle.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

# ---- RULE IMPORTS ----
from app.rules.time_rules import (
    rule_fast_cycle,
    rule_same_day_loop
)

from app.rules.amount_rules import (
    rule_amount_similarity,
    rule_exact_amount_repetition
)

from app.rules.structural_rules import (
    rule_small_closed_group,
    rule_layering
)

from app.rules.scorer import score_cycle
# ----------------------

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def find_small_cycles():
    """
    Detect unique circular trade loops of length 2–4
    """
    query = """
    MATCH p=(a:Entity)-[r:INVOICE*2..4]->(a)
    WITH
        [n IN nodes(p)[0..-1] | n.gstin] AS gstins,
        [r IN relationships(p) | toFloat(r.amount)] AS amounts,
        [r IN relationships(p) | date(r.invoice_date)] AS dates,
        size(relationships(p)) AS hops
    RETURN gstins, amounts, dates, hops
    LIMIT 100
    """

    with driver.session() as session:
        return [record.data() for record in session.run(query)]


if __name__ == "__main__":
    cycles = find_small_cycles()

    seen = set()
    unique_cycles = []

    # ---- DEDUPLICATION ----
    for c in cycles:
        normalized = tuple(sorted(c["gstins"]))
        if normalized not in seen:
            seen.add(normalized)
            unique_cycles.append(c)

    print("\n===== UNIQUE CIRCULAR TRADE CYCLES =====\n")

    for idx, c in enumerate(unique_cycles, start=1):
        gstins = c["gstins"]
        amounts = c["amounts"]
        hops = c["hops"]

        # Convert Neo4j dates → datetime
        dates = [
            datetime.strptime(str(d), "%Y-%m-%d")
            for d in c["dates"]
        ]

        node_count = len(set(gstins))
        path_length = hops

        # ---- APPLY ONLY CYCLE-RELEVANT RULES ----
        rule_results = [
            # Time-based
            rule_fast_cycle(dates),
            rule_same_day_loop(dates),

            # Amount-based
            rule_amount_similarity(amounts),
            rule_exact_amount_repetition(amounts),

            # Structural
            rule_small_closed_group(node_count),
            rule_layering(path_length)
        ]

        final_score = score_cycle(rule_results)

        # ---- OUTPUT ----
        print(f"Cycle #{idx}")
        print("GSTIN Path :", " -> ".join(gstins + [gstins[0]]))
        print("Risk Level :", final_score["risk_level"])
        print("Risk Score :", final_score["final_risk_score"])
        print("Reasons    :")
        for r in final_score["reasons"]:
            print(f"  - {r['rule_id']} ({r['risk']})")
        print("-" * 55)
