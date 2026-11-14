"""
MongoDB collection helpers.

Collections used:
  - users          : { _id, username, password_hash, created_at }
  - predictions    : { _id, user_id, disease, confidence, status,
                       explanation_json, note, image_b64, created_at }
  - chat_messages  : { _id, record_id, role, content, created_at }

All _id values are MongoDB ObjectId strings (str form).
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------- index helpers (called once at startup) ----------

def ensure_indexes(db) -> None:
    """Create indexes the first time the app boots."""
    db.users.create_index("email", unique=True)
    db.predictions.create_index("user_id")
    db.chat_messages.create_index("record_id")
