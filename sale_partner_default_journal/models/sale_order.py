# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def _prepare_invoice(self):
        result = super(SaleOrder, self)._prepare_invoice()
        result.update(
                journal_id=self.partner_invoice_id.default_sale_journal_id.id
            )
        return result

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        for this in self:
            res = super(SaleOrder, self).action_invoice_create(
                grouped=grouped, final=final
            )
            # forced to do a browse here, invoice create returns id. 
            res_objs = self.env['account.invoice'].browse(res)
            for res_obj in res_objs:
                if this.partner_invoice_id.default_return_journal_id:
                    if res_obj.type == 'out_refund':
                        res_obj.write({
                            'journal_id':
                                this.partner_invoice_id.default_return_journal_id.id
                        })
                elif this.partner_invoice_id.default_sale_journal_id:
                    res_obj.write({
                        'journal_id':
                            this.partner_invoice_id.default_sale_journal_id.id
                    })
            return res
