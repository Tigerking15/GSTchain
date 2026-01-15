# scripts/fraud_report.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# ---- RULE IMPORTS ----
from app.rules.time_rules import rule_fast_cycle, rule_same_day_loop
from app.rules.amount_rules import rule_amount_similarity, rule_exact_amount_repetition
from app.rules.structural_rules import rule_small_closed_group, rule_layering
from app.rules.behavioural_rules import rule_dormant_activation, rule_burst_invoicing
from app.rules.pan_rules import rule_pan_cluster
from app.rules.scorer import score_cycle

# ---------------------

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "neo4jpass")
    )
)

# ------------------------------------------------------------------
# STORAGE FOR FINAL RESULTS
# ------------------------------------------------------------------
gstin_scores = defaultdict(list)
gstin_reasons = defaultdict(list)

# ------------------------------------------------------------------
# 1️⃣ CYCLE FRAUD DETECTION
# ------------------------------------------------------------------
CYCLE_QUERY = """
MATCH p=(a:Entity)-[r:INVOICE*2..4]->(a)
WITH
    [n IN nodes(p)[0..-1] | n.gstin] AS gstins,
    [r IN relationships(p) | toFloat(r.amount)] AS amounts,
    [r IN relationships(p) | date(r.invoice_date)] AS dates,
    size(relationships(p)) AS hops
RETURN gstins, amounts, dates, hops
"""

with driver.session() as session:
    seen = set()

    for rec in session.run(CYCLE_QUERY):
        normalized = tuple(sorted(rec["gstins"]))
        if normalized in seen:
            continue
        seen.add(normalized)

        dates = [datetime.strptime(str(d), "%Y-%m-%d") for d in rec["dates"]]
        node_count = len(set(rec["gstins"]))
        path_length = rec["hops"]

        rules = [
            rule_fast_cycle(dates),
            rule_same_day_loop(dates),
            rule_amount_similarity(rec["amounts"]),
            rule_exact_amount_repetition(rec["amounts"]),
            rule_small_closed_group(node_count),
            rule_layering(path_length)
        ]

        result = score_cycle(rules)

        for gstin in set(rec["gstins"]):
            gstin_scores[gstin].append(result["final_risk_score"])
            gstin_reasons[gstin].extend(result["reasons"])

# ------------------------------------------------------------------
# 2️⃣ ENTITY-LEVEL FRAUD (BURST / DORMANCY)
# ------------------------------------------------------------------
ENTITY_QUERY = """
MATCH (e:Entity)-[r:INVOICE]->()
WITH e.gstin AS gstin,
     collect(date(r.invoice_date)) AS dates,
     collect(toFloat(r.amount)) AS amounts
RETURN gstin, dates, amounts
"""

with driver.session() as session:
    for rec in session.run(ENTITY_QUERY):
        dates = sorted(datetime.strptime(str(d), "%Y-%m-%d") for d in rec["dates"])

        if len(dates) < 2:
            continue

        months_dormant = (dates[-1] - dates[-2]).days // 30
        sudden_amount = max(rec["amounts"])
        invoice_count = len(dates)
        days_window = (dates[-1] - dates[0]).days or 1

        rules = [
            rule_dormant_activation(months_dormant, sudden_amount),
            rule_burst_invoicing(invoice_count, days_window)
        ]

        result = score_cycle(rules)

        if result["final_risk_score"] > 0:
            gstin_scores[rec["gstin"]].append(result["final_risk_score"])
            gstin_reasons[rec["gstin"]].extend(result["reasons"])

# ------------------------------------------------------------------
# 3️⃣ PAN-LEVEL FRAUD (SHELL COMPANIES)
# ------------------------------------------------------------------
PAN_QUERY = """
MATCH (e:Entity)
WITH e.pan AS pan, collect(e.gstin) AS gstins
RETURN pan, gstins
"""

with driver.session() as session:
    for rec in session.run(PAN_QUERY):
        rule = rule_pan_cluster(rec["pan"], rec["gstins"])
        result = score_cycle([rule])

        if result["final_risk_score"] > 0:
            for gstin in rec["gstins"]:
                gstin_scores[gstin].append(result["final_risk_score"])
                gstin_reasons[gstin].extend(result["reasons"])

# ------------------------------------------------------------------
# 📊 FINAL CONSOLIDATED REPORT
# ------------------------------------------------------------------
print("\n================ FINAL GST FRAUD REPORT ================\n")

for gstin, scores in gstin_scores.items():
    final_score = max(scores)           # conservative (highest risk wins)

    if final_score >= 80:
        risk = "HIGH"
    elif final_score >= 50:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    # Deduplicate reasons
    unique_reasons = {
        (r["rule_id"], r["risk"]) for r in gstin_reasons[gstin]
    }

    print(f"GSTIN        : {gstin}")
    print(f"Final Risk   : {risk} ({final_score})")
    print("Signals:")
    for rule_id, risk_score in unique_reasons:
        print(f"  - {rule_id} ({risk_score})")
    print("-" * 60)
