from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


ZERO = Decimal("0")
ONE_HUNDRED = Decimal("100")
MONEY_QUANT = Decimal("0.01")
PCT_QUANT = Decimal("0.01")


def parse_decimal(value: object, default: Decimal = ZERO) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default

    text = (
        text.replace("R$", "")
        .replace("r$", "")
        .replace("%", "")
        .replace(" ", "")
        .replace("\u00A0", "")
    )

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        parsed = Decimal(text)
    except InvalidOperation:
        return default
    if parsed < ZERO:
        return ZERO
    return parsed


def round_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def round_pct(value: Decimal) -> Decimal:
    return value.quantize(PCT_QUANT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PurchaseInput:
    base_price: Decimal
    ipi_rate_pct: Decimal
    st_rate_pct: Decimal
    icms_rate_pct: Decimal
    pis_rate_pct: Decimal
    cofins_rate_pct: Decimal
    credit_icms: bool
    credit_pis: bool
    credit_cofins: bool


@dataclass(frozen=True)
class SaleInput:
    pis_rate_pct: Decimal
    cofins_rate_pct: Decimal
    icms_rate_pct: Decimal
    markup_rate_pct: Decimal = ZERO
    apply_markup: bool = False


@dataclass(frozen=True)
class PricingResult:
    ipi_value: Decimal
    st_value: Decimal
    icms_purchase_value: Decimal
    pis_purchase_value: Decimal
    cofins_purchase_value: Decimal
    purchase_taxes_total: Decimal
    purchase_credits_total: Decimal
    effective_cost: Decimal
    sales_tax_rate_pct: Decimal
    sale_price_base: Decimal
    sale_price: Decimal
    markup_rate_pct: Decimal
    markup_value: Decimal
    margin_pct: Decimal
    sale_taxes_value: Decimal
    net_revenue: Decimal
    net_profit: Decimal
    real_margin_pct: Decimal


@dataclass(frozen=True)
class QuoteRecord:
    quote_id: int | None
    version: int
    status: str
    product_name: str
    category_name: str
    supplier_name: str
    owner_user: str
    notes: str
    purchase: PurchaseInput
    sale: SaleInput
    result: PricingResult
    created_at: str | None = None
    updated_at: str | None = None
