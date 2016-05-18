# coding: utf-8
# © 2016 Opener B.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Open sale order from invoice',
    'category': 'Sale',
    'author': 'Opener B.V., Odoo Community Association (OCA)',
    'version': '8.0.1.0.0',
    'website': 'https://github.com/oca/sale-worfklow',
    'summary': ("Show a button on the invoice view to open the related sale "
                "order"),
    'depends': [
        'sale',
    ],
    'data': [
        'views/account_invoice.xml',
    ],
    'installable': True,
    'licence': 'AGPL-3',
}
