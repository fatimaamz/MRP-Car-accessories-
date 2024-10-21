from odoo import fields, models, api


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    design_ids = fields.One2many('kit.design', 'bom_id', string='Dessins')

   
class MrpProductionControleQualiteWizard(models.TransientModel):
    _name = 'mrp.production.controle.qualite.wizard'

    is_conforme = fields.Boolean('Conforme')
    remarque = fields.Text('Remarque')

    #def action_save(self):
        #production_id = self.env.context.get('active_id')
        #production = self.env['mrp.production'].browse(production_id)
        #if self.is_conforme:
            #production.status_controle_qualite = 'conforme'
        #else:
            #production.status_controle_qualite = 'non_conforme'
            #"production.remarque_controle_qualite = self.remarque
        #return {'type': 'ir.actions.act_window_close'}
        
class KitDesign(models.Model):
    _name = 'kit.design'

    name = fields.Char(string='Nom')
    description = fields.Text(string='Description')
    upload_date = fields.Date(string='Date de création', default=fields.Date.today())
    pdf_file = fields.Binary(string='Fichier PDF')
    bom_id = fields.Many2one('mrp.bom', string='BOM')
    create_uid = fields.Many2one('res.users', string='Créer par', readonly=True, default=lambda self: self.env.uid)
