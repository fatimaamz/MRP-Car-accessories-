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
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)

        file_path = os.path.join(desktop_path, file_name)
        order_number = invoice.invoice_origin or ""
        
        with open(file_path, 'w') as file:
            for line in invoice.invoice_line_ids:
                if line.product_id:
                    part_number = line.product_id.default_code if line.product_id.default_code else " " * 16
                    
                    # Updated record data to match exact format from example
                    record_data = {
                        'bill': invoice.partner_id.dealer_code.ljust(5) if invoice.partner_id.dealer_code else " " * 5,  # HYCSBILL(S)
                        'part': part_number[:16].ljust(16),  # HYC16PART(16)
                        'ordd': invoice.date.strftime('%Y%m%d') if invoice.date else " " * 8,
                        'shpd': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else " " * 8,  # HYCBSHPD(8)
                        'inv': invoice.name[:12].ljust(12),  # HYC12V(12)
                        'qty': str(int(line.quantity)).zfill(7),  # HYC7QTY(7)
                        'prce': str(int(line.price_unit)).zfill(7),  # HYC7PRCE(7)
                        'amnt': str(int(line.price_subtotal)).zfill(11),  # HYC11AMNT(11)
                        'pstqst': str(int(invoice.amount_tax)).zfill(7),  # HYC7PSTQST(7)
                        'gst': "0000000",  # HYC7GST(7)
                        'totl': str(int(invoice.amount_total)).zfill(11),  # HYC11TOTL(11)
                        'invd': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else " " * 8,  # HYCBINVD(8)
                        'po': (invoice.partner_id.po or "").ljust(30),  # HYC30PO(30)
                        'dbcr': 'D',  # HYC1DBCR(1)
                        'war': ' ',  # HYC1WAR(1)
                        'desc': line.name[:30].ljust(30),  # HYC30DESC(30)
                        'wght': "00000",  # HYCSWGHT(5)
                        'frgt': "000000000",  # HYCSFRGT(9)
                        'carr': (invoice.carrier_id.name or "").ljust(30),  # HYC30CARR(30)
                        'ordr': order_number[:9].ljust(9),  # HYCBORDD(9)
                        'crdt': invoice.create_date.strftime('%Y%m%d') if invoice.create_date else " " * 8,  # HYCBCRDT(8)
                        'err': " " * 30  # HYC30ERR(30)
                    }
                    
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
