
from odoo import api, fields, models,_
import re
from datetime import datetime
import json
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import base64
from odoo.exceptions import UserError



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

   
    
    cleaned_name = fields.Char(string="Cleaned Name", compute="_compute_cleaned_name", store=True)
    installation = fields.Selection([
        ('yes', 'Oui'),
        ('no', 'Non')
    ], string='Installation Required', default='no')

    @api.depends('name')
    def _compute_cleaned_name(self):
        """
        Clean the name by removing attributes like 'CARBON CODE', 'PAINT CODE', etc., when their value is 'None' or other invalid values.
        """
        for line in self:
            cleaned_description = line.name or ''

            # Remove attribute-value pairs where the value is 'None' or 'No insert' (like 'CARBON CODE: None')
            cleaned_description = re.sub(r"(CARBON CODE|INSERT COLOR|PAINT CODE|INTERIOR COLOR|Style|Année):\s*(None|No insert|No Color)[,;]?\s*", '', cleaned_description)

            # Optionally, clean up any unnecessary commas or spaces left behind
            cleaned_description = re.sub(r"[,;]\s*$", "", cleaned_description)

            # Update the cleaned_name field with the cleaned description
            line.cleaned_name = cleaned_description.strip()

    

            
        
class StockPicking(models.Model):
    _inherit = "stock.picking"

    po = fields.Char(
        string="Po client",
        related="sale_id.client_order_ref",
       
    )

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    installation = fields.Selection([
        ('yes', 'Oui'),
        ('no', 'Non')
    ], string='Installation Required', default='no')

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

    @property
    def date_today(self):
        return datetime.today().strftime('%d/%m/%Y')
    
    
    def action_generate_invoice_pdf(self):
       
        selected_invoices = self.filtered(lambda inv: inv.move_type == 'out_invoice')
        if not selected_invoices:
            return
        date_from = self.env.context.get('date_from', fields.Date.today())
        date_to = self.env.context.get('date_to', fields.Date.today())
        
        data = {
            'date_from': date_from,
            'date_to': date_to,
        }

        return self.env.ref('lux_contacts_custom_fields.action_report_selected_invoices').report_action(
            selected_invoices, data=data
        )
        #return self.env.ref('lux_contacts_custom_fields.action_report_selected_invoices').report_action(
            #selected_invoices
        #)

   

    def _generate_pdf_report(self, invoices):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Marges et configuration
        margin_x = 50
        margin_y = height - 50
        line_height = 20

        # Titre
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin_x, margin_y, "Rapport des factures")
        margin_y -= 30

        # Date du jour
        today = date.today()
        pdf.setFont("Helvetica", 12)
        pdf.drawString(margin_x, margin_y, f"Date du jour : {today}")
        margin_y -= 20

        # Période (personnalisez si nécessaire)
        pdf.drawString(margin_x, margin_y, "Période : du ... au ...")
        margin_y -= 30

        # En-têtes des colonnes
        headers = [
            "Client", "Numéro de la facture", "Date de la facture",
            "Date d'échéance", "Montant HT", "Montant TTC"
        ]
        col_widths = [100, 100, 100, 100, 80, 80]
        pdf.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            x = margin_x + sum(col_widths[:i])
            pdf.drawString(x, margin_y, header)
        margin_y -= line_height

        # Données des factures
        pdf.setFont("Helvetica", 10)
        for invoice in invoices:
            if margin_y < 50:  # Si espace insuffisant, passer à la page suivante
                pdf.showPage()
                margin_y = height - 50

            data = [
                invoice.partner_id.name or "",
                invoice.name or "",
                str(invoice.invoice_date or ""),
                str(invoice.invoice_date_due or ""),
                f"{invoice.amount_untaxed:.2f}",
                f"{invoice.amount_total:.2f}"
            ]
            for i, value in enumerate(data):
                x = margin_x + sum(col_widths[:i])
                pdf.drawString(x, margin_y, value)
            margin_y -= line_height

        # Terminer et sauvegarder le fichier PDF
        pdf.save()
        buffer.seek(0)
        return buffer.read()
    
            
    

    delivery_price = fields.Float(
        string='Delivery Price',
        compute='_compute_delivery_price',
        store=True,
        help="The price of the delivery line in the invoice."
    )

    payment_mode = fields.Char(
        string="Mode de paiement",
        compute="_compute_payment_mode",
        store=True,
    )
    

    
  

    @api.depends('invoice_origin')
    def _compute_installation(self):
        for move in self:
            if move.invoice_origin:
                # Récupérer l'ordre de fabrication lié
                mrp_production = self.env['mrp.production'].search([
                    ('origin', '=', move.invoice_origin)
                ], limit=1)
                move.installation = mrp_production.installation if mrp_production else False
            else:
                move.installation = False

    

    def _compute_payment_mode(self):
        for record in self:
            # Get all posted payments linked to the invoice's move_id
            payments = self.env['account.payment'].search([
                ('move_id', '=', record.id),  # Match payments linked to this invoice (move_id)
                ('state', '=', 'posted')  # Only consider posted payments
            ])
    
            if payments:
                # Join the names of the journals from the filtered payments
                record.payment_mode = ", ".join(set(payments.mapped('journal_id.name')))
                
            else:
                record.payment_mode = ""
                
    

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
            
   

    payment_date = fields.Char(string='Payment Date', compute='_compute_payment_date', store=True)
    payment_journal = fields.Char(string='Payment Journal', compute='_compute_payment_date', store=True)
    ref_paym = fields.Char(string="Reference", compute='_compute_payment_ref', store=True)

    @api.depends('invoice_payments_widget')
    def _compute_payment_ref(self):
        for inv in self:
            refs = set()
            if inv.invoice_payments_widget:
                payment_data = inv.invoice_payments_widget.get('content', [])
                for payment_info in payment_data:
                    account_payment_id = payment_info.get('account_payment_id')
                    if account_payment_id:
                        # Fetch the payment record
                        payment = self.env['account.payment'].browse(account_payment_id)
                        if payment:
                            refs.add(payment.ref)
    
            # Assign the concatenated references
            inv.ref_paym = ', '.join(sorted(refs)) if refs else False

    @api.depends('invoice_payments_widget')
    def _compute_payment_date(self):
        for inv in self:
            payment_dates = set()
            payment_journals = set()
            payment_memos = set()

            if inv.invoice_payments_widget:
                # The invoice_payments_widget is already a dictionary, so no need to use json.loads
                payment_data = inv.invoice_payments_widget.get('content', [])

                for payment_info in payment_data:
                    payment_date = payment_info.get('date')
                    journal_name = payment_info.get('journal_name')
                    
                    # Add the date and journal to the respective sets to avoid duplicates
                    if payment_date:
                        payment_dates.add(payment_date)
                    if journal_name:
                        payment_journals.add(journal_name)
                   

            # Assign the extracted payment dates and journal names
            inv.payment_date = ', '.join(sorted([str(date) for date in payment_dates])) if payment_dates else False
            inv.payment_journal = ', '.join(sorted(payment_journals)) if payment_journals else False
           
            
                
    
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
   
    installation = fields.Selection([
        ('yes', 'Oui'),
        ('no', 'Non')
    ], string='Installation Required', default='no')

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
        ('concessionnaires_programme_nationaux', 'Concessionnaires Programme nationaux'),
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

"""
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        super(SaleOrder, self).action_confirm()
        for order in self:
            # Propager le champ installation vers les lignes de facture
            for line in order.order_line:
                if line.installation:
                    invoice_lines = self.env['account.move.line'].search([
                        ('sale_line_ids', 'in', line.ids)
                    ])
                    for invoice_line in invoice_lines:
                        invoice_line.write({'installation': line.installation})

                    # Propager le champ installation vers l'ordre de fabrication
                    if line.product_id.manufacture_ok:
                        production_order = self.env['mrp.production'].search([
                            ('origin', '=', order.name),
                            ('product_id', '=', line.product_id.id)
                        ])
                        for production in production_order:
                            production.move_raw_ids.write({'installation': line.installation})

"""
