# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, models


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def create_returns(self):
        partner = self.env['stock.picking'].browse(
            self.env.context.get('active_id')
        ).partner_id
        return super(
            StockReturnPicking, self.with_context(
                default_sale_journal_id = partner.default_refund_journal_id.id
            )).create_returns()


