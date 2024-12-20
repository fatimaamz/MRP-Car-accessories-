
from odoo import api, fields, models
import re


class MrpProduction(models.Model):
    _inherit = "mrp.production"


    def get_report_values(self):
        work_orders =  self.browse(self.env.context.get('active_ids', []))
        filtered_lines = []
        total_quantity = 0  # Initialize total quantity
        for line in work_orders:
            filtered_lines.append({
                'product': line.product_id.name,
                'quantity': line.product_qty,
                'date': line.picking_scheduled_date,
                'couper': "Oui" if line.is_coped else "Non",
                'reflector_type': line.product_id.reflecteur_type,
                'new_design': line.new_design,
                'logo': line.logo_inscription,
                'insert': line.insert_color,
                'interior': line.interior_color,
            })
            #total_quantity += line.product_qty  # Sum quantities
        
        return filtered_lines

 
        
    
    sale_order_partner_id = fields.Many2one(
        'res.partner',
        string='Partner from Sale Order',
        compute='_compute_sale_order_partner_id',
        store=True,
        readonly=True
    )
    
    @api.depends('origin')
    def _compute_sale_order_partner_id(self):
        for record in self:
            if record.origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                record.sale_order_partner_id = sale_order.partner_id if sale_order else False
    
class AccountMove(models.Model):
    _inherit = "account.move"

    payment_date = fields.Date(string='Payment Date', compute='_compute_payment_date', store=True)

    @api.depends('payment_ids')
    def _compute_payment_date(self):
        for move in self:
            # Find the first posted payment related to the invoice
            payment = move.payment_ids.filtered(lambda p: p.state == 'posted')
            if payment:
                move.payment_date = payment[0].payment_date  # Get the date of the first payment
            else:
                move.payment_date = False
                
    
    sale_order_partner_id = fields.Many2one(
        'res.partner',
        string='Partner from Sale Order',
        compute='_compute_sale_order_partner_id',
        store=True,
        readonly=True
    )
    
    @api.depends('invoice_origin')
    def _compute_sale_order_partner_id(self):
        for record in self:
            if record.invoice_origin:
                # Search for the related sale order using invoice_origin
                sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                record.sale_order_partner_id = sale_order.partner_id if sale_order else False




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



