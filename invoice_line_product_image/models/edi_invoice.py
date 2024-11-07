import os
from datetime import datetime
from odoo import api, fields, models,_
class AccountMove(models.Model):
    _inherit = "account.move"

    # Method to generate the TXT file for selected invoices
    def action_export_invoice(self, selected_invoice_ids):
        invoices = self.env['account.move'].browse(selected_invoice_ids)

        # Fetch the vendor name dynamically from the first invoice (assuming all selected invoices are from the same vendor)
        vendor_name = invoices[0].partner_id.name if invoices else "UnknownVendor"
        vendor_name = vendor_name.replace(" ", "")  # Remove spaces for file name compatibility
        
        # Generate the file name with vendor name and timestamp
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        file_name = f"{vendor_name}_{current_time}.txt"
        
        # Save the file to the home directory
        home_dir = os.path.expanduser("~")  # Get the current user's home directory
        file_path = os.path.join(home_dir, file_name)  # Create the full file path

        # Open the file to write the invoice data
        with open(file_path, 'w') as file:
            for invoice in invoices:
                for line in invoice.invoice_line_ids:
                    # Prepare each field
                    if line.product_id:  # Ensure product_id is valid (not False)
                        record_data = {
                            'bill': invoice.partner_id.name[:5].ljust(5),  # Example: Dealer Code (fixed length of 5 characters)
                            'part': line.product_id.default_code[:16].ljust(16) if line.product_id.default_code else "        ",  # Part Number (fixed length of 16)
                            'ordd': invoice.date_order.replace("-", "") if invoice.date_order else "        ",  # Order Date
                            'shpd': invoice.invoice_date.replace("-", ""),  # Ship Date (YYYYMMDD)
                            'inv': invoice.name[:12].ljust(12),  # Invoice Number
                            'qty': str(line.quantity).zfill(7),  # Quantity (right-justified with zero fill)
                            'prce': str(line.price_unit).zfill(7),  # Price (right-justified with zero fill)
                            'amnt': str(line.price_subtotal).zfill(11),  # Amount (right-justified with zero fill)
                            'pstqst': str(invoice.amount_tax).zfill(7),  # PST/QST (right-justified with zero fill)
                            'gst': str(invoice.amount_tax).zfill(7),  # GST (right-justified with zero fill)
                            'totl': str(invoice.amount_total).zfill(11),  # Total (right-justified with zero fill)
                            'wght': "000000000",  # Weight (optional, right-justified with zero fill)
                            'frgt': "000000000",  # Freight (zero-filled)
                            'carr': "Purolator".ljust(30),  # Carrier (left-justified)
                            'ordr': "123456789".ljust(9),  # Vendor Order Number
                            'invd': invoice.invoice_date.replace("-", ""),  # Vendor Invoice Date
                            'desc': line.name[:30].ljust(30),  # Description (left-justified)
                            'dpo': invoice.purchase_id.name[:30].ljust(30) if invoice.purchase_id else " " * 30,  # Dealer P/O Number
                            'dbcr': "D",  # Debit or Credit (D for Debit)
                            'war': "W",  # Warranty (W for Warranty)
                            'crdt': invoice.create_date.replace("-", ""),  # Vendor Creation Date
                            'err': ""  # Error Message (empty for now)
                        }

                        # Write the formatted line to the file
                        line_data = ''.join(record_data.values()) + '\n'
                        file.write(line_data)
                    else:
                        # Handle lines with no product associated (if required)
                        # You can skip these lines or write a placeholder in the file
                        continue

        return file_path  # Return file path for further use (e.g., FTP upload)
