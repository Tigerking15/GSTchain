# scripts/check_cycle.py-latest

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def find_small_cycles(amount_threshold=1000):
    query = """
    MATCH p=(a:Entity)-[r:INVOICE*2..4]->(a)
    WITH p, relationships(p) AS rels
    WITH p, rels,
         reduce(s = 0.0, r IN rels | s + toFloat(r.amount)) AS total
    WHERE total > $amt
    RETURN
      [n IN nodes(p) | n.gstin] AS gstins,
      total,
      size(rels) AS hops
    LIMIT 50
    """
    with driver.session() as session:
        result = session.run(query, amt=amount_threshold)
        return [record.data() for record in result]


if __name__ == "__main__":
    cycles = find_small_cycles()

    seen = set()
    unique_cycles = []

    for c in cycles:
        # remove last repeated gstin and normalize
        normalized = tuple(sorted(c["gstins"][:-1]))

        if normalized not in seen:
            seen.add(normalized)
            unique_cycles.append(c)

    print("Unique detected cycles:")
    for c in unique_cycles:
        print(c)