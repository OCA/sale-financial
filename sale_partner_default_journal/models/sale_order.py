# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        result = super(SaleOrder, self)._prepare_invoice()
        result.update(
            journal_id=self.partner_invoice_id.default_sale_journal_id.id
        )
        return result
