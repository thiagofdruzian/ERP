from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from erp.domain.models import parse_decimal
from erp.infrastructure.database import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SettingsRepository:
    def __init__(self, database: Database):
        self.database = database

    def get_rounding_strategy(self) -> str:
        with self.database.connect() as conn:
            row = conn.execute("SELECT value FROM app_settings WHERE key = ?", ("rounding_strategy",)).fetchone()
        if row is None:
            return "NORMAL"
        return row["value"]

    def set_rounding_strategy(self, strategy: str) -> None:
        normalized = strategy.strip().upper() or "NORMAL"
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                ("rounding_strategy", normalized, _now_iso()),
            )

    def set_min_price_rule(self, scope_type: str, scope_key: str, min_price: Decimal, is_active: bool = True) -> None:
        stype = scope_type.strip().lower()
        skey = scope_key.strip().lower()
        if stype not in {"product", "category"}:
            raise ValueError("Escopo deve ser product ou category.")
        if not skey:
            raise ValueError("Escopo vazio.")
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO min_price_rules (scope_type, scope_key, min_price, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scope_type, scope_key) DO UPDATE SET
                    min_price = excluded.min_price,
                    is_active = excluded.is_active,
                    updated_at = excluded.updated_at
                """,
                (stype, skey, float(min_price), 1 if is_active else 0, _now_iso(), _now_iso()),
            )

    def get_min_price(self, product_name: str, category_name: str) -> Decimal:
        product_key = (product_name or "").strip().lower()
        category_key = (category_name or "").strip().lower()
        with self.database.connect() as conn:
            row = None
            if product_key:
                row = conn.execute(
                    """
                    SELECT min_price
                    FROM min_price_rules
                    WHERE scope_type = 'product' AND scope_key = ? AND is_active = 1
                    """,
                    (product_key,),
                ).fetchone()
            if row is None and category_key:
                row = conn.execute(
                    """
                    SELECT min_price
                    FROM min_price_rules
                    WHERE scope_type = 'category' AND scope_key = ? AND is_active = 1
                    """,
                    (category_key,),
                ).fetchone()
        if row is None:
            return Decimal("0")
        return parse_decimal(row["min_price"])

