import os
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_export_edi_invoice(self):
        selected_invoice_ids = self.env.context.get('active_ids', [])
        if not selected_invoice_ids:
            raise UserError("No invoices selected for export.")
        
        # Iterate over each selected invoice to generate the EDI file and create attachments
        for invoice in self.env['account.move'].browse(selected_invoice_ids):  # Now `invoice` is a record, not an ID
            # Generate the EDI file for this invoice
            file_path = self.generate_edi_invoice_file(invoice)  # Passing a single invoice record
            
            # Ensure the file is accessible for download
            attachment_id = self.create_attachment(file_path, invoice)  # Pass the invoice record here
            
            # Provide the download URL for the file
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment_id.id,  # URL for downloading the file
                'target': 'self',  # Open in the same window
            }

    def generate_edi_invoice_file(self, invoice):
        """Generate the EDI file for a specific invoice."""
        vendor_name = invoice.partner_id.name.replace(" ", "") if invoice.partner_id else "UnknownVendor"
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        file_name = f"{vendor_name}_{current_time}.txt"
        file_path = os.path.join('/tmp', file_name)  # Store file in /tmp or use another directory
        
        # Open the file to write invoice data
        with open(file_path, 'w') as file:
            for line in invoice.invoice_line_ids:
                if line.product_id:  # Check if product_id is set for the line
                    # Ensure we handle missing default_code gracefully
                    part_number = line.product_id.default_code if line.product_id.default_code else " " * 16
                    # Prepare the record data
                    record_data = {
                        'bill': str(invoice.partner_id.id).zfill(5),  # Dealer Code (5 digits)
                        'part': part_number[:16].ljust(16),  # Part Number (left justified, 16 chars)
                        'ordd': invoice.date.strftime('%Y%m%d') if invoice.date else "        ",  # Order Date (YYYYMMDD)
                        'shpd': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "        ",  # Ship Date (YYYYMMDD)
                        'inv': invoice.name[:12].ljust(12),  # Invoice Number (left justified, 12 chars)
                        'qty': str(line.quantity).zfill(7),  # Shipped Quantity (right justified, zero filled, 7 chars)
                        'prce': str(line.price_unit).zfill(7),  # Unit Price (right justified, zero filled, 7 chars)
                        'amnt': str(line.price_subtotal).zfill(11),  # Amount (subtotal, right justified, zero filled, 11 chars)
                        'pstqst': str(invoice.amount_tax).zfill(7),  # PST/QST (7 chars, zero filled)
                        'gst': str(invoice.amount_tax).zfill(7),  # GST (7 chars, zero filled)
                        'totl': str(invoice.amount_total).zfill(11),  # Total (right justified, zero filled, 11 chars)
                        'wght': "000000000",  # Weight (optional, filled with zeros if not provided)
                        'frgt': "000000000",  # Freight (optional, filled with zeros if not provided)
                        'carr': "Purolator".ljust(30),  # Carrier (left justified, 30 chars)
                        'ordr': "123456789".ljust(9),  # Vendor Order Number (9 chars, left justified)
                        'invd': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "        ",  # Vendor Invoice Date (YYYYMMDD)
                        'desc': line.name[:30].ljust(30),  # Description (left justified, 30 chars)
                        'dpo': invoice.purchase_id.name[:30].ljust(30) if invoice.purchase_id else " " * 30,  # Dealer P/O Number (left justified, 30 chars)
                        'dbcr': "D",  # Debit or Credit (D for Debit)
                        'war': "W",  # Warranty (W for Warranty)
                        'crdt': invoice.create_date.strftime('%Y%m%d') if invoice.create_date else "        ",  # Vendor Creation Date (YYYYMMDD)
                        'err': ""  # Error message (empty for now)
                    }
                    # Write the formatted record data to the file
                    line_data = ''.join(record_data.values()) + '\n'
                    file.write(line_data)
                else:
                    # Handle lines with no product associated (if required)
                    continue
        
        return file_path 

    def create_attachment(self, file_path, invoice):
        """ Creates an attachment for the generated file and stores it in Odoo """
        # Read the file and create a binary attachment
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as file:
            file_data = file.read()

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'text/plain',
            'res_model': 'account.move',
            'res_id': invoice.id,  # Attach it to the current invoice
        })

        return attachment 

      
