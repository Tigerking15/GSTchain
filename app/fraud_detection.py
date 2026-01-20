# app/fraud_detection.py
"""
Fraud Detection API - Cycle Detection & Risk Analysis

This module provides:
1. Cycle detection using Neo4j graph traversal
2. Risk scoring using the rules engine
3. GSTIN analysis for suspicious patterns
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Import rules
from app.rules.structural_rules import rule_small_closed_group, rule_layering, rule_hsn_flip
from app.rules.amount_rules import rule_amount_similarity, rule_exact_amount_repetition, rule_amount_echo
from app.rules.time_rules import rule_fast_cycle, rule_same_day_loop
from app.rules.behavioural_rules import rule_dormant_activation, rule_burst_invoicing
from app.rules.scorer import score_cycle

# Try to import Neo4j - if not available, use mock data
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
    URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    USER = os.getenv("NEO4J_USER", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
except Exception:
    NEO4J_AVAILABLE = False
    driver = None

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])

# ============================================
# Schemas
# ============================================

class CycleNode(BaseModel):
    gstin: str
    name: Optional[str] = None

class DetectedCycle(BaseModel):
    cycle_id: str
    nodes: List[str]
    total_value: float
    invoice_count: int
    date_range: dict
    risk_score: int
    risk_level: str
    reasons: List[dict]

class FraudAnalysisResponse(BaseModel):
    status: str
    cycles_detected: int
    high_risk_count: int
    cycles: List[DetectedCycle]
    summary: dict

class GSTINAnalysisResponse(BaseModel):
    gstin: str
    total_invoices: int
    total_value: float
    connected_entities: int
    in_cycles: bool
    risk_indicators: List[dict]


# ============================================
# Neo4j Cycle Detection Queries
# ============================================

# This query finds unique circular trade patterns and deduplicates them
# by sorting the GSTINs so A->B->C->A and B->C->A->B are treated as the same cycle
CYCLE_DETECTION_QUERY = """
MATCH path = (start:Entity)-[:INVOICE*3..6]->(start)
WHERE ALL(r IN relationships(path) WHERE r.amount > 0)
WITH path,
     [n IN nodes(path) | n.gstin] AS raw_gstins,
     [r IN relationships(path) | r.amount] AS amounts,
     [r IN relationships(path) | r.invoice_date] AS dates,
     [r IN relationships(path) | r.invoice_hash] AS hashes,
     SIZE(nodes(path)) AS node_count

// Create a canonical form by sorting unique GSTINs (removes rotation duplicates)
WITH path, raw_gstins, amounts, dates, hashes, node_count,
     apoc.coll.toSet(raw_gstins[0..SIZE(raw_gstins)-1]) AS unique_gstins

// Sort to create canonical identifier for the cycle
WITH path, raw_gstins, amounts, dates, hashes, node_count, unique_gstins,
     apoc.coll.sort(unique_gstins) AS sorted_gstins

// Group by unique cycle (sorted GSTINs)
WITH sorted_gstins, 
     COLLECT(DISTINCT raw_gstins[0..SIZE(raw_gstins)-1])[0] AS gstins,
     COLLECT(amounts)[0] AS amounts,
     COLLECT(dates)[0] AS dates,
     COLLECT(hashes)[0] AS hashes,
     MAX(node_count) AS node_count,
     SUM(REDUCE(s = 0.0, a IN amounts | s + a)) / COUNT(*) AS total_value

RETURN DISTINCT 
    gstins,
    amounts,
    dates,
    hashes,
    node_count,
    total_value
ORDER BY total_value DESC
LIMIT 50
"""

# Simpler fallback query if APOC isn't installed
CYCLE_DETECTION_QUERY_SIMPLE = """
MATCH path = (start:Entity)-[:INVOICE*3..6]->(start)
WHERE ALL(r IN relationships(path) WHERE r.amount > 0)
WITH path,
     [n IN nodes(path) | n.gstin] AS gstins,
     [r IN relationships(path) | r.amount] AS amounts,
     [r IN relationships(path) | r.invoice_date] AS dates,
     [r IN relationships(path) | r.invoice_hash] AS hashes,
     SIZE(nodes(path)) AS node_count,
     REDUCE(s = 0.0, a IN [r IN relationships(path) | r.amount] | s + a) AS total_value
RETURN gstins, amounts, dates, hashes, node_count, total_value
ORDER BY total_value DESC
LIMIT 100
"""

GSTIN_ANALYSIS_QUERY = """
MATCH (e:Entity {gstin: $gstin})
OPTIONAL MATCH (e)-[out:INVOICE]->()
OPTIONAL MATCH ()-[in:INVOICE]->(e)
WITH e, 
     COLLECT(DISTINCT out) AS outgoing,
     COLLECT(DISTINCT in) AS incoming
RETURN e.gstin AS gstin,
       SIZE(outgoing) + SIZE(incoming) AS total_invoices,
       REDUCE(s=0, r IN outgoing | s + r.amount) + 
       REDUCE(s=0, r IN incoming | s + r.amount) AS total_value
"""


# ============================================
# API Endpoints
# ============================================

@router.get("/detect-cycles", response_model=FraudAnalysisResponse)
def detect_cycles():
    """
    Detect circular trade patterns in the invoice graph.
    Requires Neo4j to be running.
    """
    
    if not NEO4J_AVAILABLE or not driver:
        print("Neo4j driver not available")
        return get_demo_fraud_analysis()
    
    try:
        with driver.session() as session:
            # Try APOC query first, fall back to simple query
            try:
                result = session.run(CYCLE_DETECTION_QUERY)
                raw_cycles = list(result)
            except Exception as e:
                print(f"APOC query failed, using simple query: {e}")
                result = session.run(CYCLE_DETECTION_QUERY_SIMPLE)
                raw_cycles = list(result)
            
            # Python-based deduplication using frozenset of GSTINs
            seen_cycles = set()
            cycles = []
            cycle_counter = 0
            
            for record in raw_cycles:
                gstins = record["gstins"]
                amounts = record["amounts"]
                dates = record["dates"]
                node_count = record["node_count"]
                total_value = record["total_value"]
                
                # Create a canonical key for deduplication
                # Remove the last element (same as first in a cycle) and create a frozenset
                unique_gstins = list(set(gstins[:-1] if gstins[-1] == gstins[0] else gstins))
                cycle_key = frozenset(unique_gstins)
                
                # Skip if we've already seen this cycle
                if cycle_key in seen_cycles:
                    continue
                seen_cycles.add(cycle_key)
                cycle_counter += 1
                
                # Parse dates
                parsed_dates = []
                for d in dates:
                    if isinstance(d, str):
                        try:
                            parsed_dates.append(datetime.fromisoformat(d))
                        except:
                            pass
                
                # Run rules
                rule_results = []
                
                # Structural rules
                rule_results.append(rule_small_closed_group(node_count))
                rule_results.append(rule_layering(len(gstins)))
                
                # Amount rules
                rule_results.append(rule_amount_similarity(amounts))
                rule_results.append(rule_exact_amount_repetition(amounts))
                rule_results.append(rule_amount_echo(amounts))
                
                # Time rules
                if parsed_dates:
                    rule_results.append(rule_fast_cycle(parsed_dates))
                    rule_results.append(rule_same_day_loop(parsed_dates))
                
                # Score the cycle
                score = score_cycle(rule_results)
                
                cycles.append(DetectedCycle(
                    cycle_id=f"CYCLE-{cycle_counter:04d}",
                    nodes=gstins[:-1] if gstins[-1] == gstins[0] else gstins,  # Remove duplicate end node
                    total_value=total_value,
                    invoice_count=len(amounts),
                    date_range={
                        "start": min(dates) if dates else None,
                        "end": max(dates) if dates else None
                    },
                    risk_score=score["final_risk_score"],
                    risk_level=score["risk_level"],
                    reasons=score["reasons"]
                ))
            
            high_risk = sum(1 for c in cycles if c.risk_level == "HIGH")
            
            # If no cycles found, return empty result (not demo)
            return FraudAnalysisResponse(
                status="success" if cycles else "no_cycles_found",
                cycles_detected=len(cycles),
                high_risk_count=high_risk,
                cycles=cycles,
                summary={
                    "total_cycles": len(cycles),
                    "high_risk": high_risk,
                    "medium_risk": sum(1 for c in cycles if c.risk_level == "MEDIUM"),
                    "low_risk": sum(1 for c in cycles if c.risk_level == "LOW"),
                    "total_value_at_risk": sum(c.total_value for c in cycles if c.risk_level in ["HIGH", "MEDIUM"])
                }
            )
            
    except Exception as e:
        # Log the actual error
        import traceback
        print(f"Neo4j error: {e}")
        traceback.print_exc()
        return get_demo_fraud_analysis()


@router.get("/graph-stats")
def get_graph_stats():
    """
    Get stats about what's in the Neo4j graph - useful for debugging.
    """
    if not NEO4J_AVAILABLE or not driver:
        return {"error": "Neo4j not available", "neo4j_available": False}
    
    try:
        with driver.session() as session:
            # Count nodes
            node_result = session.run("MATCH (n:Entity) RETURN COUNT(n) as count")
            node_count = node_result.single()["count"]
            
            # Count relationships
            rel_result = session.run("MATCH ()-[r:INVOICE]->() RETURN COUNT(r) as count")
            rel_count = rel_result.single()["count"]
            
            # Get sample of entities
            sample_result = session.run("MATCH (n:Entity) RETURN n.gstin as gstin LIMIT 10")
            sample_entities = [r["gstin"] for r in sample_result]
            
            # Check for potential cycles (entities with both incoming and outgoing edges)
            potential_cycles = session.run("""
                MATCH (a:Entity)-[:INVOICE]->(b:Entity)-[:INVOICE]->(c:Entity)
                WHERE a <> b AND b <> c
                RETURN a.gstin as gstin1, b.gstin as gstin2, c.gstin as gstin3
                LIMIT 10
            """)
            chain_samples = [dict(r) for r in potential_cycles]
            
            return {
                "neo4j_connected": True,
                "entity_count": node_count,
                "invoice_count": rel_count,
                "sample_entities": sample_entities,
                "sample_chains": chain_samples,
                "note": "Cycles require A->B->C->A pattern (circular). Upload invoices that form a loop to detect cycles."
            }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "neo4j_available": NEO4J_AVAILABLE
        }


@router.get("/analyze-gstin/{gstin}")
def analyze_gstin(gstin: str):
    """
    Analyze a specific GSTIN for fraud indicators.
    Queries Neo4j graph for all invoices involving this GSTIN.
    """
    gstin = gstin.upper().strip()
    
    if not NEO4J_AVAILABLE or not driver:
        return {"error": "Neo4j not available", "gstin": gstin, "total_invoices": 0}
    
    try:
        with driver.session() as session:
            # Get all invoices where this GSTIN is supplier or recipient
            query = """
            MATCH (e:Entity {gstin: $gstin})
            OPTIONAL MATCH (e)-[out:INVOICE]->(recipient:Entity)
            OPTIONAL MATCH (supplier:Entity)-[incoming:INVOICE]->(e)
            WITH e,
                 COLLECT(DISTINCT {
                     hash: out.invoice_hash,
                     date: out.invoice_date,
                     amount: out.amount,
                     counterparty: recipient.gstin,
                     role: 'supplier',
                     txid: out.onchain_txid
                 }) AS outgoing_list,
                 COLLECT(DISTINCT {
                     hash: incoming.invoice_hash,
                     date: incoming.invoice_date,
                     amount: incoming.amount,
                     counterparty: supplier.gstin,
                     role: 'recipient',
                     txid: incoming.onchain_txid
                 }) AS incoming_list
            RETURN e.gstin AS gstin,
                   [x IN outgoing_list WHERE x.hash IS NOT NULL] AS as_supplier,
                   [x IN incoming_list WHERE x.hash IS NOT NULL] AS as_recipient
            """
            
            result = session.run(query, gstin=gstin)
            record = result.single()
            
            if not record or record["gstin"] is None:
                return {
                    "gstin": gstin,
                    "total_invoices": 0,
                    "as_supplier": 0,
                    "as_recipient": 0,
                    "invoices": [],
                    "message": "GSTIN not found in the invoice graph"
                }
            
            as_supplier = record["as_supplier"] or []
            as_recipient = record["as_recipient"] or []
            
            # Combine and format invoices
            invoices = []
            seen_hashes = set()
            
            for inv in as_supplier:
                if inv["hash"] and inv["hash"] not in seen_hashes:
                    seen_hashes.add(inv["hash"])
                    invoices.append({
                        "invoice_hash": inv["hash"],
                        "invoice_date": inv["date"],
                        "amount": inv["amount"],
                        "counterparty": inv["counterparty"],
                        "role": "supplier",
                        "onchain_txid": inv["txid"]
                    })
            
            for inv in as_recipient:
                if inv["hash"] and inv["hash"] not in seen_hashes:
                    seen_hashes.add(inv["hash"])
                    invoices.append({
                        "invoice_hash": inv["hash"],
                        "invoice_date": inv["date"],
                        "amount": inv["amount"],
                        "counterparty": inv["counterparty"],
                        "role": "recipient",
                        "onchain_txid": inv["txid"]
                    })
            
            # Check if in any cycles
            cycle_check = session.run("""
                MATCH path = (start:Entity {gstin: $gstin})-[:INVOICE*2..5]->(start)
                RETURN COUNT(path) > 0 AS in_cycle
            """, gstin=gstin)
            in_cycle = cycle_check.single()["in_cycle"]
            
            return {
                "gstin": gstin,
                "total_invoices": len(invoices),
                "as_supplier": len(as_supplier),
                "as_recipient": len(as_recipient),
                "total_value": sum(inv["amount"] or 0 for inv in invoices),
                "in_cycles": in_cycle,
                "invoices": invoices
            }
            
    except Exception as e:
        import traceback
        print(f"GSTIN analysis error: {e}")
        traceback.print_exc()
        return {"error": str(e), "gstin": gstin, "total_invoices": 0}


@router.get("/risk-rules")
def get_risk_rules():
    """
    Get list of all fraud detection rules and their descriptions.
    """
    return {
        "rules": [
            {
                "category": "Structural",
                "rules": [
                    {"id": "TINY_CLOSED_GROUP", "description": "Only 2-3 entities in a closed loop", "max_risk": 80},
                    {"id": "SMALL_CLOSED_GROUP", "description": "4-5 entities in a closed loop", "max_risk": 50},
                    {"id": "HEAVY_LAYERING", "description": "6+ layers of transactions", "max_risk": 60},
                    {"id": "HSN_FLIP", "description": "Product category changes suspiciously", "max_risk": 85}
                ]
            },
            {
                "category": "Amount",
                "rules": [
                    {"id": "ROUND_TRIP_<=2%", "description": "Invoice amounts within 2% of each other", "max_risk": 80},
                    {"id": "EXACT_AMOUNT_REPEATED", "description": "Same exact amount repeated 3+ times", "max_risk": 75},
                    {"id": "AMOUNT_ECHO", "description": "Amounts cluster around same value", "max_risk": 60}
                ]
            },
            {
                "category": "Time",
                "rules": [
                    {"id": "SAME_DAY_LOOP", "description": "All invoices on same day", "max_risk": 95},
                    {"id": "FAST_LOOP_<=3_DAYS", "description": "Complete cycle in 3 days", "max_risk": 90},
                    {"id": "FAST_LOOP_<=7_DAYS", "description": "Complete cycle in 7 days", "max_risk": 70}
                ]
            },
            {
                "category": "Behavioral",
                "rules": [
                    {"id": "DORMANT_GSTIN_ACTIVATION", "description": "Inactive GSTIN suddenly active with high value", "max_risk": 85},
                    {"id": "INVOICE_BURST", "description": "5+ invoices in 5 days between same parties", "max_risk": 70}
                ]
            }
        ]
    }


# ============================================
# Demo Data (when Neo4j is not available)
# ============================================

def get_demo_fraud_analysis():
    """Return demo fraud analysis data for testing without Neo4j"""
    demo_cycles = [
        DetectedCycle(
            cycle_id="CYCLE-0001",
            nodes=["27ABCDE1234F1Z5", "27XYZAB5678G2Z3", "27MNOPQ9012H3Z1"],
            total_value=4500000,
            invoice_count=6,
            date_range={"start": "2026-01-15", "end": "2026-01-18"},
            risk_score=92,
            risk_level="HIGH",
            reasons=[
                {"rule_id": "TINY_CLOSED_GROUP", "risk": 80, "details": {"nodes": 3}},
                {"rule_id": "FAST_LOOP_<=3_DAYS", "risk": 90, "details": {"duration_days": 3}},
                {"rule_id": "ROUND_TRIP_<=2%", "risk": 80, "details": {"difference_pct": 1.2}}
            ]
        ),
        DetectedCycle(
            cycle_id="CYCLE-0002",
            nodes=["27LMNOP3456K4Z7", "27QRSTU7890L5Z8", "27VWXYZ2345M6Z9", "27DEFGH6789N7Z0"],
            total_value=2800000,
            invoice_count=8,
            date_range={"start": "2026-01-10", "end": "2026-01-20"},
            risk_score=65,
            risk_level="MEDIUM",
            reasons=[
                {"rule_id": "SMALL_CLOSED_GROUP", "risk": 50, "details": {"nodes": 4}},
                {"rule_id": "AMOUNT_ECHO", "risk": 60, "details": {"rounded_amounts": [700000, 700000, 700000, 700000]}}
            ]
        ),
        DetectedCycle(
            cycle_id="CYCLE-0003",
            nodes=["27HIJKL1234P8Z1", "27STUVW5678Q9Z2"],
            total_value=950000,
            invoice_count=4,
            date_range={"start": "2026-01-19", "end": "2026-01-19"},
            risk_score=95,
            risk_level="HIGH",
            reasons=[
                {"rule_id": "TINY_CLOSED_GROUP", "risk": 80, "details": {"nodes": 2}},
                {"rule_id": "SAME_DAY_LOOP", "risk": 95, "details": {"date": "2026-01-19"}}
            ]
        )
    ]
    
    return FraudAnalysisResponse(
        status="demo_mode",
        cycles_detected=3,
        high_risk_count=2,
        cycles=demo_cycles,
        summary={
            "total_cycles": 3,
            "high_risk": 2,
            "medium_risk": 1,
            "low_risk": 0,
            "total_value_at_risk": 8250000,
            "note": "Demo data - Neo4j not connected"
        }
    )


def get_demo_gstin_analysis(gstin: str):
    """Return demo GSTIN analysis"""
    return GSTINAnalysisResponse(
        gstin=gstin,
        total_invoices=12,
        total_value=1850000,
        connected_entities=5,
        in_cycles=True,
        risk_indicators=[
            {"rule_id": "HIGH_TRANSACTION_VOLUME", "details": "12 invoices in 30 days"},
            {"rule_id": "CONNECTED_TO_FLAGGED_ENTITY", "details": "Transacted with 27XYZAB5678G2Z3"}
        ]
    )
