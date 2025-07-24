from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import base64

class AccountInvoiceReportWizard(models.TransientModel):
    _name = 'account.invoice.report.wizard'
    _description = "Wizard to generate customer invoice reports"

    company_id = fields.Many2one('res.company', string="Société", required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Client")
    date_start = fields.Date(string="Date De Début", required=True)
    date_end = fields.Date(string="Date De Fin", required=True)
    all_partners = fields.Boolean(string="Toutes", help="Sélectionner pour inclure tous les clients")
    paid_only = fields.Boolean(string="Payées", help="Inclure uniquement les factures entièrement payées")
    unpaid_only = fields.Boolean(string="Impayées", help="Inclure uniquement les factures non payées")

    @api.constrains('paid_only', 'unpaid_only')
    def _check_payment_filters(self):
        """ Vérifie que les options 'Factures Payées' et 'Factures Non Payées' ne sont pas cochées ensemble. """
        for record in self:
            if record.paid_only and record.unpaid_only:
                raise UserError("Vous ne pouvez pas sélectionner à la fois 'Factures Payées' et 'Factures Non Payées'.")
   

    def action_print_report(self):
        if self.date_start > self.date_end:
            raise UserError("La date de début doit être antérieure à la date de fin.")
        #data = self.get_invoice_report_data()
        return self.env.ref('lux_contacts_custom_fields.action_invoice_report').report_action(self)


    def action_send_report_email(self):
        #self.ensure_one()
    
        if self.date_start > self.date_end:
            raise UserError("La date de début doit être antérieure à la date de fin.")
    
        report = self.env.ref('lux_contacts_custom_fields.action_invoice_report')
        pdf_content, _ = report._render_qweb_pdf(self.id)

        filename = f"Etat_de_compte_{self.partner_id.name if self.partner_id else 'tous_les_clients'}_{self.date_start}_{self.date_end}.pdf"
    
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'account.invoice.report.wizard',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
    
        # Prépare les destinataires
        if self.all_partners:
            partners = self.env['res.partner'].search([
                ('customer_rank', '>', 0),
                ('email', '!=', False)
            ])
        else:
            if not self.partner_id or not self.partner_id.email:
                raise UserError("Veuillez sélectionner un client ayant une adresse email.")
            partners = self.partner_id
    
        # Envoie un mail par partenaire
        for partner in partners:
            email_values = {
                'subject': f"État de compte - {self.company_id.name}",
                'body_html': f"""
                    <p>Bonjour {partner.name},</p>
                    <p>Veuillez trouver ci-joint l’état de compte pour la période du {self.date_start} au {self.date_end}.</p>
                    <p>Cordialement,<br/>{self.env.user.name}</p>
                """,
                'email_to': partner.email,
                'attachment_ids': [attachment.id],
            }
            self.env['mail.mail'].create(email_values).send()
    
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Email envoyé",
                'message': "Le rapport a été envoyé avec succès.",
                'type': 'success',
                'sticky': False,
            }
        }
    

class AccountInvoiceReport(models.AbstractModel):
    _name = 'report.lux_contacts_custom_fields.invoice_report_template'
    _description = "Customer Invoice Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            return {}

        wizard = self.env['account.invoice.report.wizard'].browse(docids[0])  # Use the first wizard record
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', wizard.date_start),
            ('invoice_date', '<=', wizard.date_end),
            ('company_id', '=', wizard.company_id.id),
            ('state', '=', 'posted')
        ]

        if wizard.paid_only:
            domain.append(('payment_state', 'in', ['paid', 'in_payment']))  # Factures payées ou en paiement
        elif wizard.unpaid_only:
            domain.append(('payment_state', '=', 'not_paid'))

        if not wizard.all_partners and wizard.partner_id:
            domain.append(('partner_id', '=', wizard.partner_id.id))

        invoices = self.env['account.move'].search(domain)

        # Group invoices by partner (client)
        grouped_invoices = {}
        for invoice in invoices:
            grouped_invoices.setdefault(invoice.partner_id, []).append(invoice)

        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice.report.wizard',
            'data': {
                'date_start': wizard.date_start,
                'date_end': wizard.date_end,
                'partner_id': wizard.partner_id.name if not wizard.all_partners else 'All Customers',
                'company_id': wizard.company_id.name,
                'grouped_invoices': grouped_invoices,
                'date_today': datetime.today().strftime('%d/%m/%Y'),
            },
        }
    
  
