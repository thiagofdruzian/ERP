from decimal import Decimal
import unittest

from erp.domain.models import PurchaseInput, SaleInput, parse_decimal
from erp.domain.pricing_engine import PricingEngine


class PricingEngineTest(unittest.TestCase):
    def setUp(self):
        self.engine = PricingEngine()

    def test_ipi_and_st_do_not_credit_in_commercial_mode(self):
        purchase = PurchaseInput(
            base_price=Decimal("100"),
            ipi_rate_pct=Decimal("5"),
            st_rate_pct=Decimal("8"),
            icms_rate_pct=Decimal("18"),
            pis_rate_pct=Decimal("1.65"),
            cofins_rate_pct=Decimal("7.6"),
            credit_icms=True,
            credit_pis=True,
            credit_cofins=True,
        )
        sale = SaleInput(
            pis_rate_pct=Decimal("1.65"),
            cofins_rate_pct=Decimal("7.6"),
            icms_rate_pct=Decimal("18"),
        )

        result = self.engine.calculate_from_margin(purchase, sale, Decimal("25"))

        self.assertEqual(result.purchase_taxes_total, Decimal("40.25"))
        self.assertEqual(result.purchase_credits_total, Decimal("27.25"))
        self.assertEqual(result.effective_cost, Decimal("113.00"))

    def test_price_and_margin_are_inverse_consistent(self):
        purchase = PurchaseInput(
            base_price=Decimal("250"),
            ipi_rate_pct=Decimal("4"),
            st_rate_pct=Decimal("9"),
            icms_rate_pct=Decimal("12"),
            pis_rate_pct=Decimal("1.65"),
            cofins_rate_pct=Decimal("7.6"),
            credit_icms=True,
            credit_pis=True,
            credit_cofins=True,
        )
        sale = SaleInput(
            pis_rate_pct=Decimal("1.65"),
            cofins_rate_pct=Decimal("7.6"),
            icms_rate_pct=Decimal("18"),
        )

        from_margin = self.engine.calculate_from_margin(purchase, sale, Decimal("22"))
        from_price = self.engine.calculate_from_price(purchase, sale, from_margin.sale_price)

        self.assertEqual(from_margin.sale_price, from_price.sale_price)
        self.assertAlmostEqual(float(from_margin.margin_pct), float(from_price.margin_pct), places=2)

    def test_parse_decimal_accepts_commercial_formats(self):
        self.assertEqual(parse_decimal("R$ 1.234,56"), Decimal("1234.56"))
        self.assertEqual(parse_decimal("25,5%"), Decimal("25.5"))

    def test_markup_increases_sale_price(self):
        purchase = PurchaseInput(
            base_price=Decimal("100"),
            ipi_rate_pct=Decimal("0"),
            st_rate_pct=Decimal("0"),
            icms_rate_pct=Decimal("0"),
            pis_rate_pct=Decimal("0"),
            cofins_rate_pct=Decimal("0"),
            credit_icms=False,
            credit_pis=False,
            credit_cofins=False,
        )
        sale = SaleInput(
            pis_rate_pct=Decimal("0"),
            cofins_rate_pct=Decimal("0"),
            icms_rate_pct=Decimal("0"),
            markup_rate_pct=Decimal("10"),
            apply_markup=True,
        )

        result = self.engine.calculate_from_margin(purchase, sale, Decimal("20"))

        self.assertEqual(result.sale_price_base, Decimal("120.00"))
        self.assertEqual(result.sale_price, Decimal("132.00"))
        self.assertEqual(result.markup_value, Decimal("12.00"))


if __name__ == "__main__":
    unittest.main()
