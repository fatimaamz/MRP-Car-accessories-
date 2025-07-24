from odoo import models, fields, api,_
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
        return self.env.ref('lux_contacts_custom_fields.action_invoice_report_custom').report_action(self)


    def action_send_report_email(self):
        self.ensure_one()
    
        # Récupération du rapport PDF (id défini dans le XML)
        report = self.env.ref('lux_contacts_custom_fields.action_invoice_report_custom')
    
        # Génération du PDF à partir du rapport
        pdf_content, _ = report._render_qweb_pdf(self.id)
    
        # Préparation de la pièce jointe
        attachment = self.env['ir.attachment'].create({
            'name': 'etat_des_comptes.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
    
        # Envoi d'un mail simple avec la pièce jointe
        template = self.env.ref('mail.email_template_default')  # tu peux créer ton propre template aussi
    
        self.env['mail.mail'].create({
            'subject': 'État des comptes',
            'body_html': '<p>Veuillez trouver ci-joint le rapport des comptes.</p>',
            'email_to': self.partner_id.email,
            'attachment_ids': [(4, attachment.id)],
        }).send()
    
        return {'type': 'ir.actions.act_window_close'}

    

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
    
  
