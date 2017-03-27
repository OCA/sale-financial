# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_sale_journal_id = fields.Many2one(
        'account.journal', string='Sale journal', company_dependent=True,
        help='Use the selected journal instead of the default one',
        domain=[('type', '=', 'sale')],
    )

    default_refund_journal_id = fields.Many2one(
        'account.journal', string='Sale journal', company_dependent=True,
        help='Use the selected journal instead of the default one',
        default = lambda x: x.env.ref(
            'sale_partner_default_journal.property_res_partner_default_refund_journal_id'
        ),
        domain=[('type', '=', 'purchase')],
    )
    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + [
            'default_sale_journal_id',
        ]
