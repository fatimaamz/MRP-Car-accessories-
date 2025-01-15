# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Res partner custom fields",
    "summary": "Res partner custom fields",
    "author": "WEELITE",
    "website": "",
    "category": "Contacts",
    
    "depends": ['base','mrp_production','sale','purchase','mrp','stock'],
    "data": ["views/res_partner.xml",
             "views/sale_order_new_template.xml",
             "views/invoice_new_template.xml",
             "views/work_order_multi.xml",
             "views/single_work_order.xml"
            ],
    "installable": True,
}
