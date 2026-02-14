from __future__ import annotations

from decimal import Decimal

from erp.domain.models import (
    ONE_HUNDRED,
    ZERO,
    PricingResult,
    PurchaseInput,
    SaleInput,
    round_money,
    round_pct,
)


class PricingEngine:
    """Pure domain service for pricing calculation."""

    @staticmethod
    def _rate_to_fraction(rate_pct: Decimal) -> Decimal:
        if rate_pct <= ZERO:
            return ZERO
        return rate_pct / ONE_HUNDRED

    def calculate_from_margin(
        self, purchase: PurchaseInput, sale: SaleInput, margin_pct: Decimal
    ) -> PricingResult:
        margin_fraction = self._rate_to_fraction(margin_pct)
        base_metrics = self._build_purchase_metrics(purchase)
        sales_tax_fraction = self._sales_tax_fraction(sale)

        if sales_tax_fraction >= Decimal("0.9999"):
            raise ValueError("A soma dos impostos de venda deve ser menor que 100%.")

        target_net_revenue = base_metrics["effective_cost"] * (Decimal("1") + margin_fraction)
        sale_price_base = target_net_revenue / (Decimal("1") - sales_tax_fraction)
        sale_price = self._apply_markup_to_price(sale_price_base, sale)
        return self._build_result(
            purchase=purchase,
            sale=sale,
            sale_price_base=sale_price_base,
            sale_price=sale_price,
            base_metrics=base_metrics,
            sales_tax_fraction=sales_tax_fraction,
        )

    def calculate_from_price(
        self, purchase: PurchaseInput, sale: SaleInput, sale_price: Decimal
    ) -> PricingResult:
        base_metrics = self._build_purchase_metrics(purchase)
        sales_tax_fraction = self._sales_tax_fraction(sale)
        markup_fraction = self._markup_fraction(sale)
        if markup_fraction > ZERO:
            sale_price_base = sale_price / (Decimal("1") + markup_fraction)
        else:
            sale_price_base = sale_price

        return self._build_result(
            purchase=purchase,
            sale=sale,
            sale_price_base=sale_price_base,
            sale_price=sale_price,
            base_metrics=base_metrics,
            sales_tax_fraction=sales_tax_fraction,
        )

    def _sales_tax_fraction(self, sale: SaleInput) -> Decimal:
        return (
            self._rate_to_fraction(sale.pis_rate_pct)
            + self._rate_to_fraction(sale.cofins_rate_pct)
            + self._rate_to_fraction(sale.icms_rate_pct)
        )

    def _markup_fraction(self, sale: SaleInput) -> Decimal:
        if not sale.apply_markup:
            return ZERO
        return self._rate_to_fraction(sale.markup_rate_pct)

    def _apply_markup_to_price(self, base_price: Decimal, sale: SaleInput) -> Decimal:
        markup_fraction = self._markup_fraction(sale)
        if markup_fraction <= ZERO:
            return base_price
        return base_price * (Decimal("1") + markup_fraction)

    def _build_purchase_metrics(self, purchase: PurchaseInput) -> dict[str, Decimal]:
        base = purchase.base_price
        ipi = base * self._rate_to_fraction(purchase.ipi_rate_pct)
        st = base * self._rate_to_fraction(purchase.st_rate_pct)
        icms = base * self._rate_to_fraction(purchase.icms_rate_pct)
        pis = base * self._rate_to_fraction(purchase.pis_rate_pct)
        cofins = base * self._rate_to_fraction(purchase.cofins_rate_pct)

        purchase_taxes_total = ipi + st + icms + pis + cofins

        # Commercial resale mode: IPI and ST never generate credit.
        credits_total = ZERO
        if purchase.credit_icms:
            credits_total += icms
        if purchase.credit_pis:
            credits_total += pis
        if purchase.credit_cofins:
            credits_total += cofins

        effective_cost = base + purchase_taxes_total - credits_total
        return {
            "ipi": ipi,
            "st": st,
            "icms": icms,
            "pis": pis,
            "cofins": cofins,
            "purchase_taxes_total": purchase_taxes_total,
            "credits_total": credits_total,
            "effective_cost": effective_cost,
        }

    def _build_result(
        self,
        purchase: PurchaseInput,
        sale: SaleInput,
        sale_price_base: Decimal,
        sale_price: Decimal,
        base_metrics: dict[str, Decimal],
        sales_tax_fraction: Decimal,
    ) -> PricingResult:
        sale_taxes_value = sale_price * sales_tax_fraction
        net_revenue = sale_price - sale_taxes_value
        net_profit = net_revenue - base_metrics["effective_cost"]
        markup_value = sale_price - sale_price_base

        if base_metrics["effective_cost"] > ZERO:
            margin_pct = (net_profit / base_metrics["effective_cost"]) * ONE_HUNDRED
            real_margin_pct = (net_profit / base_metrics["effective_cost"]) * ONE_HUNDRED
        else:
            margin_pct = ZERO
            real_margin_pct = ZERO

        return PricingResult(
            ipi_value=round_money(base_metrics["ipi"]),
            st_value=round_money(base_metrics["st"]),
            icms_purchase_value=round_money(base_metrics["icms"]),
            pis_purchase_value=round_money(base_metrics["pis"]),
            cofins_purchase_value=round_money(base_metrics["cofins"]),
            purchase_taxes_total=round_money(base_metrics["purchase_taxes_total"]),
            purchase_credits_total=round_money(base_metrics["credits_total"]),
            effective_cost=round_money(base_metrics["effective_cost"]),
            sales_tax_rate_pct=round_pct(sales_tax_fraction * ONE_HUNDRED),
            sale_price_base=round_money(sale_price_base),
            sale_price=round_money(sale_price),
            markup_rate_pct=round_pct(sale.markup_rate_pct if sale.apply_markup else ZERO),
            markup_value=round_money(markup_value),
            margin_pct=round_pct(margin_pct),
            sale_taxes_value=round_money(sale_taxes_value),
            net_revenue=round_money(net_revenue),
            net_profit=round_money(net_profit),
            real_margin_pct=round_pct(real_margin_pct),
        )
