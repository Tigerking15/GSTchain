# app/graph.py--new
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def upsert_edge(supplier_gstin: str, recipient_gstin: str, invoice_hash: str, invoice_date: str, amount: float, onchain_txid: str, ingestion_id: str):
    q = """
    MERGE (s:Entity {gstin:$supplier})
    MERGE (r:Entity {gstin:$recipient})
    CREATE (s)-[t:INVOICE {
        invoice_hash:$invoice_hash,
        invoice_date:$invoice_date,
        amount:$amount,
        onchain_txid:$onchain_txid,
        ingestion_id:$ingestion_id
    }]->(r)
    RETURN id(s) as sid, id(r) as rid
    """
    with driver.session() as session:
        res = session.run(q, supplier=supplier_gstin, recipient=recipient_gstin, invoice_hash=invoice_hash,
                          invoice_date=invoice_date, amount=amount, onchain_txid=onchain_txid, ingestion_id=ingestion_id)
        return res.single()
