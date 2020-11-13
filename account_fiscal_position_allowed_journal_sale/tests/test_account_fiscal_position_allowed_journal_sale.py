# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestAccountFiscalPositionAllowedJournalSale(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountFiscalPositionAllowedJournalSale, cls).setUpClass()

        # MODELS
        cls.account_model = cls.env["account.account"]
        cls.fiscal_position_model = cls.env["account.fiscal.position"]
        cls.journal_model = cls.env["account.journal"]
        cls.partner_model = cls.env["res.partner"]
        cls.product_product_model = cls.env["product.product"]
        cls.sale_order_model = cls.env["sale.order"]

        # INSTANCES
        cls.fiscal_position_01 = cls.fiscal_position_model.create(
            {"name": "Fiscal position 01"}
        )
        cls.journal_01 = cls.journal_model.search([("type", "=", "sale")], limit=1)
        cls.journal_02 = cls.journal_01.copy()
        cls.partner_01 = cls.partner_model.search([], limit=1)
        cls.product_01 = cls.product_product_model.search(
            [("type", "=", "service")], limit=1
        )
        cls.sale_order_01 = cls.sale_order_model.create(
            {
                "partner_id": cls.partner_01.id,
                "fiscal_position_id": cls.fiscal_position_01.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Sale order line 01",
                            "product_id": cls.product_01.id,
                            "product_uom_qty": 1,
                            "price_unit": 1,
                        },
                    )
                ],
            }
        )
        cls.sale_order_01.action_confirm()

    def test_01(self):
        """
        Data:
            - A confirmed sale order with a fiscal position
            - Exactly one sale journal allowed on the fiscal position
        Test case:
            - Create the invoice from the sale order
        Expected result:
            - The allowed sale journal is set on the invoice
        """
        self.fiscal_position_01.allowed_journal_ids = [(6, 0, self.journal_02.ids)]
        invoice = self.sale_order_01._create_invoices()
        self.assertEqual(invoice.journal_id, self.journal_02)

    def test_02(self):
        """
        Data:
            - A confirmed sale order with no fiscal position
        Test case:
            - Create the invoice from the sale order
        Expected result:
            - Invoice created
        """
        self.sale_order_01.fiscal_position_id = False
        invoice = self.sale_order_01._create_invoices()
        self.assertTrue(invoice)

    def test_03(self):
        """
        Data:
            - A confirmed sale order with a fiscal position
            - Two sale journals allowed on the fiscal position
        Test case:
            - Create the invoice from the sale order
        Expected result:
            - The default sale journal is set on the invoice
        """
        self.fiscal_position_01.allowed_journal_ids = [
            (6, 0, (self.journal_01 | self.journal_02).ids)
        ]
        invoice = self.sale_order_01._create_invoices()
        self.assertEqual(invoice.journal_id, self.journal_01)
