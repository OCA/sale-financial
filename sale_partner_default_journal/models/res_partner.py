# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_sale_journal_id = fields.Many2one(
        'account.journal', string='Sale journal', company_dependent=True,
        help='Use the selected journal instead of the default one',
        domain=[('type', '=', 'sale')]
    )

    default_return_journal_id = fields.Many2one(
        'account.journal', string='Sale returns journal',
        company_dependent=True,
        domain=[('type', '=', 'purchase')],
        help='Use the selected journal for all returns of this customer,'
        'it can be set by modifying the system property' 
        '\'partner_default_return_journal_id\''
    )

    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + [
            'default_sale_journal_id',
        ]
