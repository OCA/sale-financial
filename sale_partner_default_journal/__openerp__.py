# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Default journal for partners",
    "version": "9.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Sales",
    "summary": "Allows you to define a default journal per partner for "
    "generating invoices",
    "depends": [
        'sale',
        'sale_stock_picking_return_invoicing',
    ],
    "data": [
        "views/res_partner.xml",
        "data/ir_property.xml",
    ],
}
