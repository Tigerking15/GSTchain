# scripts/check_cycle.py
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def find_small_cycles(max_length=4, amount_threshold=1000):
    q = """
    MATCH p=(a:Entity)-[r:INVOICE*1..$k]->(a)
    WITH p, relationships(p) AS rels
    WHERE size(rels) >=2 AND size(rels) <= $k
    // compute total round-trip amount
    WITH p, reduce(s=0.0, r IN rels | s + toFloat(r.amount)) AS total
    WHERE total > $amt
    RETURN [n IN nodes(p) | n.gstin] as gstins, total, size(rels) as hops
    LIMIT 50
    """
    with driver.session() as s:
        res = s.run(q, k=max_length, amt=amount_threshold)
        return [r.data() for r in res]

if __name__ == "__main__":
    print(find_small_cycles())
