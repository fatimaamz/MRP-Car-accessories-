from odoo import models, fields, api

class WhatsAppComposer(models.TransientModel):
    _inherit = 'whatsapp.composer'

    contact_id = fields.Many2one('res.partner', string='Contact')
    
    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        if self.contact_id:
            self.phone = self.contact_id.mobile or self.contact_id.phone
