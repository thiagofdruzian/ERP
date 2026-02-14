from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal

from erp.domain.models import (
    PricingResult,
    PurchaseInput,
    QuoteRecord,
    SaleInput,
    parse_decimal,
)
from erp.infrastructure.database import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decimal_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError("Invalid non-serializable value")


class QuoteRepository:
    def __init__(self, database: Database):
        self.database = database

    def save(self, quote: QuoteRecord) -> QuoteRecord:
        now_iso = _now_iso()
        purchase_payload = json.dumps(asdict(quote.purchase), default=_decimal_default)
        sale_payload = json.dumps(asdict(quote.sale), default=_decimal_default)
        result_payload = json.dumps(asdict(quote.result), default=_decimal_default)

        if quote.quote_id is None:
            saved = self._insert_quote(
                quote=quote,
                now_iso=now_iso,
                purchase_payload=purchase_payload,
                sale_payload=sale_payload,
                result_payload=result_payload,
            )
        else:
            saved = self._update_quote(
                quote=quote,
                now_iso=now_iso,
                purchase_payload=purchase_payload,
                sale_payload=sale_payload,
                result_payload=result_payload,
            )

        self._insert_version_snapshot(saved)
        return saved

    def _insert_quote(
        self,
        quote: QuoteRecord,
        now_iso: str,
        purchase_payload: str,
        sale_payload: str,
        result_payload: str,
    ) -> QuoteRecord:
        with self.database.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO quotes (
                    version,
                    status,
                    product_name,
                    category_name,
                    supplier_name,
                    owner_user,
                    notes,
                    purchase_payload,
                    sale_payload,
                    result_payload,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    quote.status,
                    quote.product_name,
                    quote.category_name,
                    quote.supplier_name,
                    quote.owner_user,
                    quote.notes,
                    purchase_payload,
                    sale_payload,
                    result_payload,
                    now_iso,
                    now_iso,
                ),
            )
            new_id = int(cursor.lastrowid)
        return self.get(new_id)

    def _update_quote(
        self,
        quote: QuoteRecord,
        now_iso: str,
        purchase_payload: str,
        sale_payload: str,
        result_payload: str,
    ) -> QuoteRecord:
        with self.database.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE quotes
                   SET version = version + 1,
                       status = ?,
                       product_name = ?,
                       category_name = ?,
                       supplier_name = ?,
                       owner_user = ?,
                       notes = ?,
                       purchase_payload = ?,
                       sale_payload = ?,
                       result_payload = ?,
                       updated_at = ?
                 WHERE id = ? AND version = ?
                """,
                (
                    quote.status,
                    quote.product_name,
                    quote.category_name,
                    quote.supplier_name,
                    quote.owner_user,
                    quote.notes,
                    purchase_payload,
                    sale_payload,
                    result_payload,
                    now_iso,
                    quote.quote_id,
                    quote.version,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError("A cotacao foi alterada por outro processo. Recarregue o historico.")
        return self.get(int(quote.quote_id))

    def _insert_version_snapshot(self, quote: QuoteRecord) -> None:
        purchase_payload = json.dumps(asdict(quote.purchase), default=_decimal_default)
        sale_payload = json.dumps(asdict(quote.sale), default=_decimal_default)
        result_payload = json.dumps(asdict(quote.result), default=_decimal_default)

        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO quote_versions (
                    quote_id,
                    version,
                    status,
                    product_name,
                    category_name,
                    supplier_name,
                    owner_user,
                    notes,
                    purchase_payload,
                    sale_payload,
                    result_payload,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quote.quote_id,
                    quote.version,
                    quote.status,
                    quote.product_name,
                    quote.category_name,
                    quote.supplier_name,
                    quote.owner_user,
                    quote.notes,
                    purchase_payload,
                    sale_payload,
                    result_payload,
                    quote.updated_at or _now_iso(),
                ),
            )

    def get(self, quote_id: int) -> QuoteRecord:
        with self.database.connect() as conn:
            row = conn.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
        if row is None:
            raise ValueError("Cotacao nao encontrada.")
        return self._row_to_record(row)

    def get_version(self, quote_id: int, version: int) -> QuoteRecord:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT quote_id as id, version, status, product_name, category_name, supplier_name,
                       owner_user, notes, purchase_payload, sale_payload, result_payload,
                       created_at, created_at as updated_at
                FROM quote_versions
                WHERE quote_id = ? AND version = ?
                """,
                (quote_id, version),
            ).fetchone()
        if row is None:
            raise ValueError("Versao da cotacao nao encontrada.")
        return self._row_to_record(row)

    def list_versions(self, quote_id: int) -> list[dict[str, str]]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT version, status, created_at
                FROM quote_versions
                WHERE quote_id = ?
                ORDER BY version DESC
                """,
                (quote_id,),
            ).fetchall()

        return [
            {
                "version": str(row["version"]),
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_recent(self, limit: int = 200, filters: dict[str, str] | None = None) -> list[dict[str, str]]:
        safe_limit = max(1, min(limit, 1000))
        filters = filters or {}

        clauses = ["1=1"]
        params: list[object] = []

        status = (filters.get("status") or "").strip().upper()
        supplier = (filters.get("supplier") or "").strip().lower()
        product = (filters.get("product") or "").strip().lower()
        user_name = (filters.get("owner_user") or "").strip().lower()
        date_from = (filters.get("date_from") or "").strip()
        date_to = (filters.get("date_to") or "").strip()

        if status and status != "TODOS":
            clauses.append("status = ?")
            params.append(status)
        if supplier:
            clauses.append("LOWER(supplier_name) LIKE ?")
            params.append(f"%{supplier}%")
        if product:
            clauses.append("LOWER(product_name) LIKE ?")
            params.append(f"%{product}%")
        if user_name:
            clauses.append("LOWER(owner_user) LIKE ?")
            params.append(f"%{user_name}%")
        if date_from:
            clauses.append("updated_at >= ?")
            params.append(f"{date_from}T00:00:00")
        if date_to:
            clauses.append("updated_at <= ?")
            params.append(f"{date_to}T23:59:59")

        where_sql = " AND ".join(clauses)

        with self.database.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, version, status, product_name, category_name, supplier_name, owner_user, updated_at
                  FROM quotes
                 WHERE {where_sql}
              ORDER BY updated_at DESC
                 LIMIT ?
                """,
                (*params, safe_limit),
            ).fetchall()

        return [
            {
                "id": str(row["id"]),
                "version": str(row["version"]),
                "status": row["status"],
                "product_name": row["product_name"],
                "category_name": row["category_name"],
                "supplier_name": row["supplier_name"],
                "owner_user": row["owner_user"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def duplicate(self, quote_id: int, owner_user: str) -> QuoteRecord:
        original = self.get(quote_id)
        duplicated = QuoteRecord(
            quote_id=None,
            version=1,
            status="RASCUNHO",
            product_name=f"{original.product_name} (Copia)",
            category_name=original.category_name,
            supplier_name=original.supplier_name,
            owner_user=owner_user,
            notes=original.notes,
            purchase=original.purchase,
            sale=original.sale,
            result=original.result,
        )
        return self.save(duplicated)

    def _row_to_record(self, row) -> QuoteRecord:
        purchase_payload = json.loads(row["purchase_payload"])
        sale_payload = json.loads(row["sale_payload"])
        result_payload = json.loads(row["result_payload"])

        purchase = PurchaseInput(
            base_price=parse_decimal(purchase_payload["base_price"]),
            ipi_rate_pct=parse_decimal(purchase_payload["ipi_rate_pct"]),
            st_rate_pct=parse_decimal(purchase_payload["st_rate_pct"]),
            icms_rate_pct=parse_decimal(purchase_payload["icms_rate_pct"]),
            pis_rate_pct=parse_decimal(purchase_payload["pis_rate_pct"]),
            cofins_rate_pct=parse_decimal(purchase_payload["cofins_rate_pct"]),
            credit_icms=bool(purchase_payload["credit_icms"]),
            credit_pis=bool(purchase_payload["credit_pis"]),
            credit_cofins=bool(purchase_payload["credit_cofins"]),
        )
        sale = SaleInput(
            pis_rate_pct=parse_decimal(sale_payload["pis_rate_pct"]),
            cofins_rate_pct=parse_decimal(sale_payload["cofins_rate_pct"]),
            icms_rate_pct=parse_decimal(sale_payload["icms_rate_pct"]),
            markup_rate_pct=parse_decimal(sale_payload.get("markup_rate_pct")),
            apply_markup=bool(sale_payload.get("apply_markup", False)),
        )
        sale_price = parse_decimal(result_payload["sale_price"])
        sale_price_base = parse_decimal(result_payload.get("sale_price_base"), default=sale_price)

        result = PricingResult(
            ipi_value=parse_decimal(result_payload["ipi_value"]),
            st_value=parse_decimal(result_payload["st_value"]),
            icms_purchase_value=parse_decimal(result_payload["icms_purchase_value"]),
            pis_purchase_value=parse_decimal(result_payload["pis_purchase_value"]),
            cofins_purchase_value=parse_decimal(result_payload["cofins_purchase_value"]),
            purchase_taxes_total=parse_decimal(result_payload["purchase_taxes_total"]),
            purchase_credits_total=parse_decimal(result_payload["purchase_credits_total"]),
            effective_cost=parse_decimal(result_payload["effective_cost"]),
            sales_tax_rate_pct=parse_decimal(result_payload["sales_tax_rate_pct"]),
            sale_price_base=sale_price_base,
            sale_price=sale_price,
            markup_rate_pct=parse_decimal(result_payload.get("markup_rate_pct")),
            markup_value=parse_decimal(result_payload.get("markup_value")),
            margin_pct=parse_decimal(result_payload["margin_pct"]),
            sale_taxes_value=parse_decimal(result_payload["sale_taxes_value"]),
            net_revenue=parse_decimal(result_payload["net_revenue"]),
            net_profit=parse_decimal(result_payload["net_profit"]),
            real_margin_pct=parse_decimal(result_payload["real_margin_pct"]),
        )

        return QuoteRecord(
            quote_id=int(row["id"]),
            version=int(row["version"]),
            status=row["status"],
            product_name=row["product_name"],
            category_name=row["category_name"] or "",
            supplier_name=row["supplier_name"],
            owner_user=row["owner_user"] if "owner_user" in row.keys() else "admin",
            notes=row["notes"],
            purchase=purchase,
            sale=sale,
            result=result,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
