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
    dnet_total = fields.Float(
        string='DNET Total',
        compute='_compute_dnet_total',
        store=True,
        help="Total DNET incluant les taxes et les frais de transport"
    )


    def get_details(self):
        for record in self:
            picking = self.env['stock.picking'].search([
                ('origin', '=', record.invoice_origin)
            ], limit=1)
            
           
            record.tracking = picking.numero_suivi if picking else False
            record.carrier_id = picking.carrier_id if picking else False
            
     

    #------------------- Nissan EDI Invoice ------------------------------------
    def action_export_custom_edi_nissan_invoice(self):
        selected_invoice_ids = self.env.context.get('active_ids', [])
        if not selected_invoice_ids:
            raise UserError("No invoices selected for export.")

        for invoice in self.env['account.move'].browse(selected_invoice_ids):
            file_path = self.generate_custom_edi_nissan_invoice_file(invoice)
            attachment_id = self.create_attachment(file_path, invoice)
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment_id.id,
                'target': 'new',
            }

    def generate_custom_edi_nissan_invoice_file(self, invoice):
        vendor_name = invoice.partner_id.name.replace(" ", "")
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        file_name = f"{vendor_name}_{current_time}.txt"
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)

        file_path = os.path.join(desktop_path, file_name)
        
        with open(file_path, 'w') as file:
            # Format invoice date as YYYYMMDD
            invoice_date = invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else ""
            
            # Convert amounts to integers and pad with zeros
            nci_cost = str(int(invoice.amount_untaxed * 100)).zfill(9)  # NCI Cost Total
            dnet_total = str(int(invoice.dnet_total * 100)).zfill(9)
            transport = str(int(invoice.freight_cost * 100)).zfill(9) if invoice.freight_cost else "000000000"
            gst_tax = str(int(invoice.amount_tax * 100)).zfill(6)  # GST/FED TX
            pst_tax = "000000"  # PST/PRV TX (set to 0 in example)
            
            # Format quantity with leading zeros
            qty = str(int(invoice.pcs if invoice.pcs else 0)).zfill(3)
            
            # Format each section with proper spacing
            dealer_and_invoice = f"{invoice.partner_id.dealer_code}{invoice.name}"  # No padding, exact values
            date_and_item = f"{invoice_date}LUXNCIBILL"
            numbers_section = f"0000{qty}{nci_cost}{dnet_total}{transport}{gst_tax}{pst_tax}D"
            
            # Combine sections with proper spacing
            line_data = f"{dealer_and_invoice}              {date_and_item}          {numbers_section}\n"
            
            file.write(line_data)

        return file_path

    def create_attachment(self, file_path, invoice):
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

    #------------------- Hyundai EDI Invoice ------------------------------------
    def action_export_edi_invoice(self):
        selected_invoice_ids = self.env.context.get('active_ids', [])
        if not selected_invoice_ids:
            raise UserError("No invoices selected for export.")

        for invoice in self.env['account.move'].browse(selected_invoice_ids):
            file_path = self.generate_edi_hyundai_invoice_file(invoice)
            attachment_id = self.create_attachment(file_path, invoice)
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment_id.id,
                'target': 'new',
            }

    def generate_edi_hyundai_invoice_file(self, invoice):
        """ Generate the EDI invoice file based on Hyundai specifications """
        vendor_name = invoice.partner_id.name.replace(" ", "") 
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        file_name = f"{vendor_name}_{current_time}.txt"
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)

        file_path = os.path.join(desktop_path, file_name)
        
        with open(file_path, 'w') as file:
            for line in invoice.invoice_line_ids:
                if line.product_id:
                    # Convert decimal amounts to integers (multiply by 100 and round)
                    unit_price = int(round(line.price_unit * 100))
                    subtotal = int(round(line.price_subtotal * 100))
                    total_tax = int(round(invoice.amount_tax * 100))
                    total = int(round(invoice.dnet_total * 100))
                    freight = int(round(invoice.freight_cost * 100)) if invoice.freight_cost else 0
                    weight = int(round(invoice.weight)) if invoice.weight else 0
                    
                    # Split tax amount between PST/QST and GST (adjust as needed)
                    pst_amount = total_tax // 2
                    gst_amount = total_tax - pst_amount
                    
                    # Safely handle default_code
                    default_code = line.product_id.default_code or "X"
                    
                    record_data = {
                        'BILL': str(invoice.partner_id.dealer_code or "0").zfill(5),
                        'PART': default_code[:13].ljust(13),  # Now safe even if default_code was False
                        'space_3': " " * 3,
                        '0' : "0" * 8,
                        'SHPD': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "0" * 8,  # Required, A(8)
                        'INV': invoice.name[:12].ljust(12),  # Required, A(12)
                        'space_6': " " * 6,
                        'QTY': str(int(line.quantity)).zfill(7),  # Required, N(7)
                        'PRCE': str(unit_price).zfill(7),  # Required, N(7)

                        'AMNT': str(subtotal).zfill(11),  # Required, N(11)
                        'PSTQST': str(pst_amount).zfill(7),  # Required, N(7)
                        'GST': str(gst_amount).zfill(7),  # Required, N(7)
                        'TOTL': str(total).zfill(11),  # Required, N(11)
                        'WGHT': str(weight).zfill(9),  # Optional, N(9)
                        'space_39': " " * 39,
                        # 'FRGT$': str(freight).zfill(9),  # Optional, N(9)
                        'ORDD': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "0" * 8,  # Optional, A(8)
                        'CARR': "X" * 30,  # Optional, A(30)
                        'ORDR': (invoice.invoice_origin or "0"*9).ljust(9),  # Optional, A(9)
                        'INVD': invoice.invoice_date.strftime('%Y%m%d') if invoice.invoice_date else "0" * 8,  # Required, A(8)
                        'DBCR': 'D' if invoice.move_type == 'out_invoice' else 'C',  # Required, A(1)
                        'DESC': (" ").ljust(30),  # Optional, A(30)
                        'DPO': (" ").ljust(30),  # Required, A(30)
                    }
                    
                    record_string = f"{record_data['BILL']}{record_data['PART']}{record_data['space_3']}{record_data['0']}" \
                                    f"{record_data['SHPD']}{record_data['INV']}{record_data['space_6']}{record_data['QTY']}" \
                                    f"{record_data['PRCE']}{record_data['AMNT']}{record_data['PSTQST']}{record_data['GST']}" \
                                    f"{record_data['TOTL']}{record_data['WGHT']}{record_data['space_39']}{record_data['ORDD']}" \
                                    f"{record_data['CARR']}{record_data['ORDR']}{record_data['INVD']}{record_data['DBCR']}" \
                                    f"{record_data['DESC']}{record_data['DPO']}\n"

                    file.write(record_string)



        return file_path

    def create_attachment(self, file_path, invoice):
        """ Creates an attachment for the generated file and stores it in Odoo """
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

    @api.depends('amount_total', 'freight_cost')
    def _compute_dnet_total(self):
        for record in self:
            record.dnet_total = record.amount_total + (record.freight_cost or 0.0)
