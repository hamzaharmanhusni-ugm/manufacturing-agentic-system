"""Storage connectors. Default = Docker databases (docker-compose.yml).
Set MAS_STORAGE=local to run without Docker (SQLite files and JSON documents under data/stores/)."""
import json
import os
import threading

from shared.config import STORES

LOCAL = os.getenv("MAS_STORAGE", "docker").lower() == "local"
PG = os.getenv("MAS_PG_URL", "postgresql+psycopg2://mas:mas_local_dev@127.0.0.1:5442")
MONGO_URL = os.getenv("MAS_MONGO_URL", "mongodb://127.0.0.1:27027")


def sql_url(db: str) -> str:
    """manufacturer and supplier: PostgreSQL databases (SQLite file when local)."""
    if LOCAL:
        STORES.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{STORES / (db + '.db')}"
    return f"{PG}/{db}"


_engines = {}


def engine(db: str):
    from sqlalchemy import create_engine
    if db not in _engines:
        _engines[db] = create_engine(sql_url(db), pool_pre_ping=True)
    return _engines[db]


class Collection:
    """Shipping document collection: MongoDB, or a JSON file when local."""
    lock = threading.Lock()

    def __init__(self, name):
        self.name = name
        self.path = STORES / "shipping" / f"{name}.json"

    def _mongo(self):
        from pymongo import MongoClient
        if not hasattr(Collection, "_client"):
            Collection._client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
        return Collection._client["shipping"][self.name]

    def find(self):
        if LOCAL:
            return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        docs = list(self._mongo().find().sort("_id", 1))
        for d in docs:
            if not isinstance(d.get("_id"), str):
                d.pop("_id", None)  # ObjectId is not JSON; our own ids are strings
        return docs

    def save(self, docs):
        with self.lock:
            if LOCAL:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(json.dumps(docs, indent=1), encoding="utf-8")
                return
            col = self._mongo()
            col.delete_many({})
            if docs:
                col.insert_many([dict(d) for d in docs])

    def count(self):
        return len(self.find()) if LOCAL else self._mongo().estimated_document_count()
