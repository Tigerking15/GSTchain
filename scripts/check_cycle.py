#!/usr/bin/env python3
"""
Find small cycles (circular trades) in the Neo4j graph.

Usage:
  python scripts/check_cycle.py
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def find_small_cycles(max_length=4, amount_threshold=0.0, limit=50):
    try:
        max_length = int(max_length)
    except Exception:
        raise ValueError("max_length must be an integer")
    if max_length < 1 or max_length > 12:
        raise ValueError("max_length must be between 1 and 12 (safe bound)")

    rel_pattern = f"r:INVOICE*1..{max_length}"

    cypher = f"""
    MATCH p=(a:Entity)-[{rel_pattern}]->(a)
    WITH p, relationships(p) AS rels
    WITH p,
         [x IN rels | coalesce(x.invoice_hash, "")] AS invoice_hashes,
         [x IN rels | coalesce(x.txid, "")] AS txids,
         reduce(s = 0.0, x IN rels | s + coalesce(x.amount, 0.0)) AS total_amount,
         size(rels) AS path_length,
         [n IN nodes(p) | n.gstin] AS gstin_path
    WHERE total_amount >= $amt
    RETURN gstin_path, invoice_hashes, txids, total_amount, path_length
    ORDER BY total_amount DESC, path_length ASC
    LIMIT $limit
    """

    with driver.session() as s:
        rows = s.run(cypher, amt=float(amount_threshold), limit=int(limit)).data()
        return rows

if __name__ == "__main__":
    max_length = 4
    amount_threshold = 0.0
    limit = 100

    cycles = find_small_cycles(max_length=max_length, amount_threshold=amount_threshold, limit=limit)
    if not cycles:
        print("No cycles found (matching the criteria).")
    else:
        print(f"Found {len(cycles)} cycles (up to length {max_length}):\n")
        for i, c in enumerate(cycles, 1):
            gstin_path = " -> ".join(c["gstin_path"])
            print(f"{i}) path_length={c['path_length']} total_amount={c['total_amount']}")
            print(f"   gstins: {gstin_path}")
            print(f"   invoice_hashes: {c['invoice_hashes']}")
            print(f"   txids: {c['txids']}\n")
