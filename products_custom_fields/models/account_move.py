from odoo import models, fields,api,_
import os
import base64
from datetime import datetime
from odoo.exceptions import ValidationError




                

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    dealer_code = fields.Char(string="Dealer Code",  help="Unique HACC Dealer Code")
    po = fields.Char(string="PO",  help="PO client")

   
 

    #@api.constrains('dealer_code')
    #def _check_dealer_code_unique(self):
        #for record in self:
            #if record.dealer_code:
                #existing = self.search([
                   # ('dealer_code', '=', record.dealer_code),
                    #('id', '!=', record.id)
                #], limit=1)
                #if existing:
                    #raise ValidationError("The Dealer Code must be unique.")
  
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    num_stock = fields.Char(string='N° Stock')
    num_lx = fields.Char(string="Numéro LX")
    pcs = fields.Integer(string='PCS')
    weight = fields.Float(string='Poids')
    tracking = fields.Char(string='Numéro de tracking',compute="_compute_picking_details", store=True)
    custom_clearance = fields.Char(string='Dédouanement')
    transport = fields.Char(string='Transport')
    freight_cost = fields.Float(string="Freight Cost")
    #carrier_id = fields.Many2one('delivery.carrier', string="Carrier")
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        compute="get_details",
        string="Transport",
        help="The delivery carrier associated with this invoice."
    )
    numero_serie = fields.Char(string='Numéro Série')
    tvp = fields.Char(string='TVP/P.S.T')
    tps = fields.Char(string='TPS/Q.S.T ')
    luxncibill_number = fields.Char(
        string="Numéro de Pièce Unique",
        help="Numéro de pièce unique",
    )

    @api.model
    def create(self, vals):
        if not vals.get("name") or vals["name"] == "/":
            seq = self.env["ir.sequence"].next_by_code("account.move") or "/"
            vals["name"] = "KX" + seq  # Ensure it follows "KX+number" format
        return super().create(vals)

    def get_details(self):
        for record in self:
            picking = self.env['stock.picking'].search([
                ('origin', '=', record.invoice_origin)
            ], limit=1)
            
           
            record.tracking = picking.numero_suivi if picking else False
            record.carrier_id = picking.carrier_id if picking else False
            
     

    #------------------- Hyundai Edi Invoice------------------------------------
    def action_export_edi_invoice(self):
        selected_invoice_ids = self.env.context.get('active_ids', [])
        if not selected_invoice_ids:
            raise UserError("No invoices selected for export.")

        for invoice in self.env['account.move'].browse(selected_invoice_ids):
            # Generate the EDI file
            file_path = self.generate_edi_invoice_file(invoice)
            
            # Ensure the file is accessible for download
            attachment_id = self.create_attachment(file_path, invoice)
            
            # Provide the download URL for the file
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment_id.id,  # URL for downloading the file
                'target': 'new',  # Open in the same window
            }

    def generate_edi_invoice_file(self, invoice):
        """ Generate the EDI invoice file based on the given invoice """
        vendor_name = invoice.partner_id.name.replace(" ", "") 
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        file_name = f"{vendor_name}_{current_time}.txt"
        #file_path = os.path.join('/tmp', file_name)  # Store file in /tmp or use another directory
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)  # Crée le répertoire si nécessaire

        file_path = os.path.join(desktop_path, file_name)
        order_number = ""
        if invoice.invoice_origin:
            # Check if the origin is linked to a sale order (customer order)
            #sale_order = self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
            #if sale_order:
            order_number = invoice.invoice_origin
            #else:
                #purchase_order = self.env['purchase.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
                #order_number = purchase_order.name 
        
        # Open the file to write invoice data
        with open(file_path, 'w') as file:
            for line in invoice.invoice_line_ids:
                if line.product_id:  # Check if product_id is set for the line
                    # Ensure we handle missing default_code gracefully
                    part_number = line.product_id.default_code if line.product_id.default_code else " " * 16
                    # Prepare the record data
                    record_data = {
                        #'bill': str(invoice.partner_id.dealer_code).zfill(5),  # Dealer Code (5 digits)
                        'bill': invoice.partner_id.dealer_code.ljust(5) if invoice.partner_id.dealer_code else " " * 5,  # Dealer Code (5 chars, left justified)
                        'part': part_number[:16].ljust(16),  # Part Number (left justified, 16 chars)
                        'ordd': invoice.date.strftime('%Y%m%d') if invoice.date else "        ",  # Order Date (YYYYMMDD)
                        'shpd': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "        ",  # Ship Date (YYYYMMDD)
                        'inv': invoice.name[:12].ljust(12),  # Invoice Number (left justified, 12 chars)
                        'qty': str(line.quantity).zfill(7),  # Shipped Quantity (right justified, zero filled, 7 chars)
                        'prce': str(line.product_id.dnet).zfill(7),  # Unit Price (right justified, zero filled, 7 chars)
                        'amnt': str(line.price_subtotal).zfill(11),  # Amount (subtotal, right justified, zero filled, 11 chars)
                        'pstqst': str(invoice.amount_tax).zfill(7),  # PST/QST (7 chars, zero filled)
                        'gst': str(invoice.amount_tax).zfill(7),  # GST (7 chars, zero filled)
                        'totl': str(invoice.amount_total).zfill(11),  # Total (right justified, zero filled, 11 chars)
                        'wght': str(invoice.weight).zfill(9),  # Weight (optional, filled with zeros if not provided)
                        'frgt': str(int(invoice.freight_cost)).zfill(9) if invoice.freight_cost else "000000000",  # Freight (optional, filled with zeros if not provided)
                        'carr': invoice.carrier_id.name[:30].ljust(30) if invoice.carrier_id else " " * 30,  # Carrier name (left justified, 30 chars)
                        'ordr': order_number[:9].ljust(9),  # Vendor Order Number (9 chars, left justified)
                        'invd': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "        ",  # Vendor Invoice Date (YYYYMMDD)
                        'desc': line.name[:30].ljust(30),  # Description (left justified, 30 chars)
                        'dpo': invoice.purchase_id.name[:30].ljust(30) if invoice.purchase_id else " " * 30,  # Dealer P/O Number (left justified, 30 chars)
                        'dbcr': 'D' if invoice.move_type == 'out_invoice' else 'C', # Debit or Credit (D for Debit)
                        'war': "W",  # Warranty (W for Warranty)
                        'crdt': invoice.create_date.strftime('%Y%m%d') if invoice.create_date else "        ",  # Vendor Creation Date (YYYYMMDD)
                        'err': ""  # Error message (empty for now)
                    }
                    # Write the formatted record data to the file
                    line_data = ''.join(record_data.values()) + '\n'
                    file.write(line_data)

        return file_path

    def create_attachment(self, file_path, invoice):
        """ Creates an attachment for the generated file and stores it in Odoo """
        # Read the file and create a binary attachment
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as file:
            file_data = file.read()  # Read the file content

        # Base64 encode the binary file data before saving it to Odoo
        encoded_file_data = base64.b64encode(file_data).decode('utf-8')

        # Create the attachment record
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': encoded_file_data,  # Store the Base64 encoded content here
            'mimetype': 'text/plain',
            'res_model': 'account.move',
            'res_id': invoice.id,  # Attach it to the current invoice
        })

        return attachment  # Return the attachment record




    #------------------- Nissan Edi Invoice------------------------------------

     

    # Method for the second EDI export button
    def action_export_custom_edi_nissan_invoice(self):
        selected_invoice_ids = self.env.context.get('active_ids', [])
        if not selected_invoice_ids:
            raise UserError("No invoices selected for export.")

        for invoice in self.env['account.move'].browse(selected_invoice_ids):
            file_path = self.generate_custom_edi_nissan_invoice_file(invoice)
            attachment_id = self.create_attachment2(file_path, invoice)
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment_id.id,
                'target': 'new',
            }

    def generate_custom_edi_nissan_invoice_file(self, invoice):
        """ Generate the custom EDI invoice file based on the second format """
        vendor_name = invoice.partner_id.name.replace(" ", "")
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        file_name = f"{vendor_name}_custom_{current_time}.txt"
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)

        file_path = os.path.join(desktop_path, file_name)
        luxncibill_line = next((line for line in invoice.invoice_line_ids if line.product_id.default_code == "LUXNCIBILL"), None)

        if not luxncibill_line:
            raise ValueError("No product line with reference 'LUXNCIBILL' found in the invoice.")
        with open(file_path, 'w') as file:
            #for line in invoice.invoice_line_ids:
                # Build the new record data based on the specified format
                record_data = {
                    #'dealer_code': str(invoice.partner_id.dealer_code).zfill(5),
                    'dealer_code': invoice.partner_id.dealer_code.ljust(5) if invoice.partner_id.dealer_code else " " * 5,  # Dealer Code (5 chars, left justified)
                    'invoice_number': invoice.name[:20].ljust(20),
                    #'invoice_date': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else " " * 8,
                    'item_ref_number': "LUXNCIBILL".ljust(20),  # Numéro de pièce (fixé à LUXNCIBILL)
                    'wholesale_amount': str(invoice.amount_total_signed).zfill(9),
                    #'item_ref_number': (line.product_id.default_code[:20].ljust(20) if line.product_id and line.product_id.default_code else " " * 20),
                    #'num_items': str(line.quantity).zfill(7),
                    #'wholesale_amount': str(int(line.price_subtotal * 100)).zfill(9),  # Assuming 2 decimal places
                    #'dealer_net_amount': "0" * 9,  # Placeholder; customize if needed
                    #'freight_amount': str(int(invoice.freight_cost * 100)).zfill(9) if invoice.freight_cost else "0" * 9,
                    #'gst_amount': str(int(invoice.amount_tax * 100)).zfill(7),
                    #'pst_amount': str(int(invoice.amount_tax * 100)).zfill(7),  # Same as GST for simplicity; adjust as needed
                    #'record_type': 'D' if invoice.move_type == 'out_invoice' else 'C'  # 'D' for debit, 'C' for credit
                }
                
                # Write formatted record data to the file
                line_data = ''.join(record_data.values()) + '\n'
                file.write(line_data)

        return file_path

    def create_attachment2(self, file_path, invoice):
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as file:
            file_data = file.read()
        encoded_file_data = base64.b64encode(file_data).decode('utf-8')

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': encoded_file_data,
            'mimetype': 'text/plain',
            'res_model': 'account.move',
            'res_id': invoice.id,
        })
        return attachment
