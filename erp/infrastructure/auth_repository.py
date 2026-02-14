from __future__ import annotations

from datetime import datetime, timezone

from erp.infrastructure.database import Database
from erp.infrastructure.security import hash_password, verify_password


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuthRepository:
    def __init__(self, database: Database):
        self.database = database

    def ensure_default_admin(self) -> None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, role, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("admin", hash_password("admin123"), "GERENCIA", 1, _now_iso()),
                )

    def authenticate(self, username: str, password: str) -> dict[str, str] | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT username, password_hash, role, is_active
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
            if row is None or int(row["is_active"]) != 1:
                return None
            if not verify_password(password, row["password_hash"]):
                return None

            conn.execute(
                "UPDATE users SET last_login_at = ? WHERE username = ?",
                (_now_iso(), username),
            )

        return {"username": row["username"], "role": row["role"]}

    def list_users(self) -> list[dict[str, str]]:
        with self.database.connect() as conn:
            rows = conn.execute(
                "SELECT username, role, is_active, created_at, last_login_at FROM users ORDER BY username"
            ).fetchall()
        return [
            {
                "username": row["username"],
                "role": row["role"],
                "is_active": str(row["is_active"]),
                "created_at": row["created_at"],
                "last_login_at": row["last_login_at"] or "",
            }
            for row in rows
        ]

    def create_user(self, username: str, password: str, role: str) -> None:
        if not username.strip():
            raise ValueError("Usuario invalido.")
        if len(password) < 6:
            raise ValueError("Senha deve ter ao menos 6 caracteres.")
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username.strip(), hash_password(password), role.strip() or "COMERCIAL", 1, _now_iso()),
            )

