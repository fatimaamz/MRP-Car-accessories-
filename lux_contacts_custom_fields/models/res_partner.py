
from odoo import api, fields, models
import re

class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_partner_info = fields.Text(
        string="Sale Order Partner Info",
        compute="_compute_sale_order_partner_info",
        store=True
    )

    @api.depends("invoice_origin")
    def _compute_sale_order_partner_info(self):
        for record in self:
            partner_info = ""
            if record.invoice_origin:
                # Search for the related sale order using invoice_origin
                sale_order = self.env["sale.order"].search([("name", "=", record.invoice_origin)], limit=1)
                if sale_order and sale_order.partner_id:
                    partner = sale_order.partner_id
                    # Format the partner address information
                    address = f"{partner.name or ''}\n"
                    address += f"{partner.street or ''}, {partner.city or ''}\n"
                    address += f"{partner.zip or ''}, {partner.country_id.name or ''}"
                    partner_info = address
            record.sale_order_partner_info = partner_info
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    insert_color = fields.Char(string="Insert Color", compute="_compute_insert_color", store=True)

    @api.depends('name')
    def _compute_insert_color(self):
        """
        Extract the "Insert Color" value from the description.
        """
        pattern = r"Insert Color:\s*(.+)\s*\((\w+)\)"
        for line in self:
            match = re.search(pattern, line.name or '')
            if match:
                line.insert_color = f"{match.group(1).strip()} ({match.group(2).strip()})"
            else:
                line.insert_color = False

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    dealer_Code=fields.Char(string='Code du concessionnaire')
    type_client = fields.Selection([
        ('Concessionnaires Régulier', 'Concessionnaires Régulier'),
        ('Concessionnaires Programme nationaux', 'Concessionnaires Programme nationaux'),
        ('Distributeur', 'Distributeur'),
        ('Particulier', 'Particulier'),
        ('Fabriquant majeur', 'Fabriquant majeur'),
        ('E-comm Distributeur', 'E-comm Distributeur'),
        ('Carrosserie', 'Carrosserie'),
    ], string='Type client')
    type_fournisseur = fields.Selection([
        ('Service', 'Service'),
        ('Matériel', 'Matériel'),
        ('Service / Matériel','Service / Matériel'),
    ], string='Type de fournisseur')

    region = fields.Selection([
        ('MTL', 'MTL'),
        ('GTA', 'GTA'),
        ('LUX', 'LUX'),
    ], string='Région')

    type_paiement = fields.Selection([
        ('Per Order','Per Order'),
        ('OEM','OEM'),
        ('45 days','45 days'),
        ('Monthly','Monthly'),
    ], string='Type de paiement')

    oem = fields.Selection([
        ('HMA', 'HMA'),
        ('HYC', 'HYC'),
        ('NCI', 'NCI'),
    ], string='OEM')

    installation = fields.Selection([
        ('Oui', 'Oui'),
        ('Non', 'Non'),
    ], string='Installation')

    prov = fields.Selection([
        ('AB', 'AB'),
        ('BC', 'BC'),
        ('IN', 'IN'),
        ('ON', 'ON'),
        ('CT', 'CT'),
        ('FL', 'FL'),
        ('IL', 'IL'),
        ('MB', 'MB'),
        ('NB', 'NB'),
        ('NL', 'NL'),
        ('NS', 'NS'),
        ('NJ', 'NJ'),
        ('PBA', 'PBA'),
        ('PE', 'PE'),
        ('PEI', 'PEI'),
        ('QC', 'QC'),
        ('SK', 'SK'),
        ('VA', 'VA'),
        ('YT', 'YT'),
        ('NC', 'NC'),
    ], string='Prov')



