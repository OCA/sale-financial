# coding: utf-8
# © 2016 Opener B.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models
from openerp.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    has_sale_order = fields.Boolean(compute='_get_has_sale_order')

    @api.multi
    def _get_has_sale_order(self):
        """ Determines if the button to show sale order will be shown on the
        invoice """
        sales = self.env['sale.order'].search(
            [('invoice_ids', 'in', self.ids)])
        invoice_ids = sales.mapped('invoice_ids').ids
        for invoice in self:
            invoice.has_sale_order = invoice.id in invoice_ids

    @api.multi
    def open_sale_order(self):
        sale_ids = self.env['sale.order'].search(
            [('invoice_ids', 'in', self.ids)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Orders'),
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'form' if len(sale_ids) == 1 else 'tree,form',
            'res_id': sale_ids[0] if len(sale_ids) == 1 else False,
            'domain': [('id', 'in', sale_ids)],
        }
