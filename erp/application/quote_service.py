from __future__ import annotations

from decimal import Decimal

from erp.domain.models import PricingResult, PurchaseInput, QuoteRecord, SaleInput
from erp.domain.pricing_engine import PricingEngine
from erp.infrastructure.quote_repository import QuoteRepository


class QuoteService:
    def __init__(self, pricing_engine: PricingEngine, repository: QuoteRepository):
        self.pricing_engine = pricing_engine
        self.repository = repository

    def calculate_from_margin(
        self, purchase: PurchaseInput, sale: SaleInput, margin_pct: Decimal
    ) -> PricingResult:
        return self.pricing_engine.calculate_from_margin(purchase, sale, margin_pct)

    def calculate_from_price(
        self, purchase: PurchaseInput, sale: SaleInput, sale_price: Decimal
    ) -> PricingResult:
        return self.pricing_engine.calculate_from_price(purchase, sale, sale_price)

    def apply_business_rules(
        self,
        purchase: PurchaseInput,
        sale: SaleInput,
        result: PricingResult,
        rounding_strategy: str,
        min_sale_price: Decimal,
    ) -> PricingResult:
        adjusted_price = result.sale_price

        strategy = (rounding_strategy or "NORMAL").strip().upper()
        if strategy == "X90":
            int_part = int(adjusted_price)
            adjusted_price = Decimal(f"{int_part}.90")
            if adjusted_price < result.sale_price:
                adjusted_price = Decimal(f"{int_part + 1}.90")
        elif strategy == "X99":
            int_part = int(adjusted_price)
            adjusted_price = Decimal(f"{int_part}.99")
            if adjusted_price < result.sale_price:
                adjusted_price = Decimal(f"{int_part + 1}.99")

        if min_sale_price > Decimal("0") and adjusted_price < min_sale_price:
            adjusted_price = min_sale_price

        if adjusted_price == result.sale_price:
            return result
        return self.pricing_engine.calculate_from_price(purchase, sale, adjusted_price)

    def save_quote(self, quote: QuoteRecord) -> QuoteRecord:
        return self.repository.save(quote)

    def get_quote(self, quote_id: int) -> QuoteRecord:
        return self.repository.get(quote_id)

    def list_recent_quotes(
        self, limit: int = 200, filters: dict[str, str] | None = None
    ) -> list[dict[str, str]]:
        return self.repository.list_recent(limit=limit, filters=filters)

    def list_quote_versions(self, quote_id: int) -> list[dict[str, str]]:
        return self.repository.list_versions(quote_id)

    def get_quote_version(self, quote_id: int, version: int) -> QuoteRecord:
        return self.repository.get_version(quote_id, version)

    def duplicate_quote(self, quote_id: int, owner_user: str) -> QuoteRecord:
        return self.repository.duplicate(quote_id, owner_user)
