import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neo4j import GraphDatabase

from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase
from datetime import datetime
from app.rules.behavioural_rules import rule_dormant_activation, rule_burst_invoicing
from app.rules.scorer import score_cycle

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

QUERY = """
MATCH (e:Entity)-[r:INVOICE]->()
WITH e.gstin AS gstin,
     collect(date(r.invoice_date)) AS dates,
     collect(toFloat(r.amount)) AS amounts
RETURN gstin, dates, amounts
"""

with driver.session() as session:
    for rec in session.run(QUERY):
        dates = sorted([datetime.strptime(str(d), "%Y-%m-%d") for d in rec["dates"]])

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
            print("GSTIN:", rec["gstin"], result)
