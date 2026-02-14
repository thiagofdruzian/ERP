from __future__ import annotations

from datetime import datetime, timezone

from erp.infrastructure.database import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditRepository:
    def __init__(self, database: Database):
        self.database = database

    def log(self, username: str, action: str, entity_type: str, entity_id: str, details: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (username, action, entity_type, entity_id, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, action, entity_type, entity_id, details, _now_iso()),
            )

    def list_recent(self, limit: int = 300) -> list[dict[str, str]]:
        safe_limit = max(1, min(limit, 2000))
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT username, action, entity_type, entity_id, details, created_at
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "username": row["username"],
                "action": row["action"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "details": row["details"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

