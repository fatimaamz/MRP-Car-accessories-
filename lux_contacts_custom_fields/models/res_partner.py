
from odoo import api, fields, models
import re
import datetime

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cleaned_name = fields.Char(
        string='Cleaned Description',
        compute='_compute_cleaned_name',
        store=True,
        help="The cleaned version of the description without unwanted variant values."
    )

    @api.depends('name', 'product_id')
    def _compute_cleaned_name(self):
        for line in self:
            if not line.name:
                line.cleaned_name = False
                continue
            
            # Initial cleaned description is the original
            cleaned_description = line.name

            # Now we check the product's variants to hide values if None
            if line.product_id and line.product_id.product_template_attribute_value_ids:
                for attribute_value in line.product_id.product_template_attribute_value_ids:
                    if attribute_value and attribute_value.name in ['None', 'No insert']:
                        # If the attribute value is None or No insert, we hide it in the description
                        cleaned_description = re.sub(r'(\b' + re.escape(attribute_value.name) + r':\s*None|No insert|,?\s*)', '', cleaned_description)

            # Handle the removal of unnecessary spaces, commas, and blank fields
            cleaned_description = re.sub(r'\s{2,}', ' ', cleaned_description)  # Replace multiple spaces by one
            cleaned_description = re.sub(r'\s*,\s*', ', ', cleaned_description)  # Remove spaces around commas

            # Remove any trailing commas and spaces
            cleaned_description = re.sub(r',\s*$', '', cleaned_description)

            # Clean up any leading or trailing spaces
            cleaned_description = cleaned_description.strip()

            # Store the cleaned description
            line.cleaned_name = cleaned_description
        
        
class StockPicking(models.Model):
    _inherit = "stock.picking"

    po = fields.Char(
        string="Po client",
        related="sale_id.client_order_ref",
       
    )

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    #picking_id = fields.Many2one('stock.picking', string="Stock Picking", compute="_compute_picking_id")
    #picking_scheduled_date = fields.Datetime(related='picking_id.scheduled_date', string="Must Ship By")

    
    #@api.depends('origin')  
    #def _compute_picking_id(self):
        #for production in self:
            #picking = self.env['stock.picking'].search([
                #('origin', '=', production.origin),  
                #('state', 'not in', ['cancel'])
            #], limit=1)

            #production.picking_id = picking.id if picking else False

    work_order_multi = fields.Char(
        string="Work Order Multi",
        readonly=True,
        copy=False
    )

    @api.model
    def create(self, vals):
        if 'work_order_multi' not in vals:
            vals['work_order_multi'] = self.env['ir.sequence'].next_by_code('mrp.production.work_order_multi') or 'WM00000'
        return super(MrpProduction, self).create(vals)

    
    def get_report_values(self):
        work_orders =  self.browse(self.env.context.get('active_ids', []))
        filtered_lines = []
        total_quantity = 0  # Initialize total quantity
        for line in work_orders:
            filtered_lines.append({
                'image':line.selected_image,
                'name':line.name,
                'product': line.product_id.name,
                'quantity': line.product_qty,
                'date': line.picking_scheduled_date,
                'placer': "Oui" if line.place_status=='place' else "Non",
                'couper': "Oui" if line.is_coped else "Non",
                'reflector_type': line.product_id.reflecteur_type,
                'new_design': line.new_design,
                'logo': line.logo_inscription,
                'insert': line.insert_color,
                'interior': line.interior_color,
            })
            #total_quantity += line.product_qty  # Sum quantities
        
        return filtered_lines

 
        
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        compute='_compute_sale_order',
        store=True,
       
    )
    #po_client = fields.Char(string="PO client",related='sale_order_id.ref')
    sale_order_partner_id = fields.Many2one(
        'res.partner',
        string='Partner from Sale Order',
        compute='_compute_sale_order_partner_id',
        store=True,
        readonly=True
    )
    
    @api.depends('origin')
    def _compute_sale_order(self):
        for record in self:
            if record.origin:  
                sale_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                record.sale_order_id = sale_order.id if sale_order else False
            else:
                record.sale_order_id = False
    
    @api.depends('origin')
    def _compute_sale_order_partner_id(self):
        for record in self:
            if record.origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                record.sale_order_partner_id = sale_order.partner_id if sale_order else False
    
class AccountMove(models.Model):
    _inherit = "account.move"

    delivery_price = fields.Float(
        string='Delivery Price',
        compute='_compute_delivery_price',
        store=True,
        help="The price of the delivery line in the invoice."
    )

    @api.depends('invoice_line_ids')
    def _compute_delivery_price(self):
        for record in self:
            delivery_category = self.env['product.category'].search([('id', '=', 5)], limit=1)
            
            if delivery_category:
                # Filter invoice lines by products in the 'Delivery Services' category
                delivery_lines = record.invoice_line_ids.filtered(
                    lambda line: line.product_id.categ_id == delivery_category
                )
                record.delivery_price = sum(delivery_lines.mapped('price_subtotal'))
            else:
                record.delivery_price = 0.0
                

    picking_scheduled_date = fields.Datetime(
        string="Ship date",
        compute="_compute_picking_details"
       
    )
    sales_team_id = fields.Many2one(
        comodel_name='crm.team',
        string="Sales Team",
        related='invoice_user_id.sale_team_id',
        store=True
    )
    picking_name = fields.Char(
        string="Tracking Name",
        compute="_compute_picking_details",
        store=True
    )
    numero_suivi = fields.Char(
        string="Tracking Number",
        compute="_compute_picking_details",
        store=True
    )
    #carrier_id = fields.Many2one(
        #comodel_name='delivery.carrier',
       # compute="_compute_picking_details",
       # string="Transport",
        #help="The delivery carrier associated with this invoice."
   # )

    delivery_date = fields.Datetime(
        string='Delivery Date',
        related='picking_id.scheduled_date',
        store=True,
        help="The scheduled delivery date for the related delivery order."
    )
    tracking = fields.Char(
        string='Numéro de tracking',
        related='picking_id.numero_suivi',
        store=True,
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string="Transport",
        related='picking_id.carrier_id',
        store=True,
        help="The delivery carrier associated with this invoice."
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string="Delivery Order",
        compute='_compute_picking_id',
        store=True,
        help="The delivery order linked to this invoice."
    )

    @api.depends('invoice_origin')
    def _compute_picking_id(self):
        for record in self:
            if record.invoice_origin:
                record.picking_id = self.env['stock.picking'].search([
                    ('origin', '=', record.invoice_origin),
                    ('state', '!=', 'cancel')  # Optional: Ensure it's not a canceled picking
                ], limit=1)
            else:
                record.picking_id = False
                

    def _compute_picking_details(self):
        for record in self:
            picking = self.env['stock.picking'].search([
                ('origin', '=', record.invoice_origin)
            ], limit=1)
            
            record.picking_name = picking.name if picking else False
            #record.numero_suivi = picking.numero_suivi if picking else False
            #record.carrier_id = picking.carrier_id if picking else False
            record.picking_scheduled_date = picking[0].scheduled_date if picking else False

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
    interior_color = fields.Char(string="Interior Color", compute="_compute_interior_color", store=True)

    @api.depends('name')
    def _compute_interior_color(self):
        """
        Extract the "Interior Color" value from the description.
        """
        pattern = r"Interior Color:\s*(.+)\s*\((\w+)\)"
        for line in self:
            match = re.search(pattern, line.name or '')
            if match:
                line.interior_color = f"{match.group(1).strip()} ({match.group(2).strip()})"
            else:
                line.interior_color = False
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

    type_groupe_1 = fields.Selection(
        [
            ('dom', 'Dealer-OEM-MTL'),
            ('dm', 'Dealer-MTL'),
           
        ],
        string="Type Groupe ",
        help="Select the group type for the first category: Dealer, OEM, or MTL."
    )

    
    #dealer_Code=fields.Char(string='Code du concessionnaire')
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



