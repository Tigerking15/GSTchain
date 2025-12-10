# app/models.py
from sqlalchemy import Column, String, DateTime, Float, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://devuser:devpass@localhost:5432/gst_detector")
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class InvoiceMeta(Base):
    __tablename__ = "invoices"
    id = Column(String, primary_key=True, index=True)
    ingestion_id = Column(String, index=True)
    supplier_gstin = Column(String, index=True)
    recipient_gstin = Column(String, index=True)
    invoice_id = Column(String, index=True)
    invoice_date = Column(DateTime)
    invoice_hash = Column(String, index=True)
    object_path = Column(Text)
    onchain_txid = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
