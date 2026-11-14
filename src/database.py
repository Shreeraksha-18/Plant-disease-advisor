import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "plant_advisor")

_client: MongoClient = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


def get_db():
    """FastAPI dependency — yields the MongoDB database object."""
    client = get_client()
    db = client[DB_NAME]
    try:
        yield db
    finally:
        pass  # MongoClient manages its own connection pool; no per-request close needed
