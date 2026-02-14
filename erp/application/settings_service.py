from __future__ import annotations

from decimal import Decimal

from erp.infrastructure.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self, repository: SettingsRepository):
        self.repository = repository

    def get_rounding_strategy(self) -> str:
        return self.repository.get_rounding_strategy()

    def set_rounding_strategy(self, strategy: str) -> None:
        self.repository.set_rounding_strategy(strategy)

    def set_min_price_rule(
        self, scope_type: str, scope_key: str, min_price: Decimal, is_active: bool = True
    ) -> None:
        self.repository.set_min_price_rule(
            scope_type=scope_type, scope_key=scope_key, min_price=min_price, is_active=is_active
        )

    def get_min_price(self, product_name: str, category_name: str) -> Decimal:
        return self.repository.get_min_price(product_name=product_name, category_name=category_name)

