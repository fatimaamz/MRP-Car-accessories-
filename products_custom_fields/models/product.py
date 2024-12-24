# -*- coding: utf-8 -*-

from odoo import models,fields,api



class YearModel(models.Model):
    _name = 'year.model'
    _description = 'Year Model'

    name = fields.Integer(string='Année', required=True, unique=True)


class ProductMark(models.Model):
    _name = 'product.modele'
    _description = 'Product model'

    name = fields.Char(string='model', required=True)
class ProductSousModele(models.Model):
    _name = 'product.sousmodele'
    _description = 'Product Sous modele'

    name = fields.Char(string='Sous modèle', required=True)

class ProductStyle(models.Model):
    _name = 'product.style'
    _description = 'Product Style'

    name = fields.Char(string='Name', required=True)
class ProductMarque(models.Model):
    _name = 'product.marque'
    _description = 'Product Brand'

    name = fields.Char(string='Name', required=True)
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qr_code_uploaded = fields.Image("QR Code" ,max_width=512, max_height=512)
    reflecteur_type = fields.Selection(
        [('oui', 'Oui'), ('non', 'Non')],
        string="Type Réflecteur",
        default='non',  
        help="Indicate whether the product has a Réflecteur Type."
    )
    price_line_ids = fields.One2many('product.price.line', 'product_id', string='Liste des prix')
    year_ids = fields.Many2many('year.model', string='Année')
    product_type = fields.Selection([
        ('Exterior', 'Exterior'),
        ('Moulding', 'Moulding'),
        ('Interior', 'Interior'),
        ('Grill', 'Grill')
    ], string='Type')

    priceA = fields.Float(string='Prix A')
    priceB = fields.Float(string='Prix B')
    priceC = fields.Float(string='Prix C')
    priceD = fields.Float(string='Prix D')

    modele_id = fields.Many2one('product.modele', string='Modèle')
    sous_model_id = fields.Many2one('product.sousmodele', string='Sous modèle')
    style_id = fields.Many2one('product.style', string='Style')
    marque_id = fields.Many2one('product.marque', string='Marque')
            
class ProductProduct(models.Model):
    _inherit = 'product.product'

    reflecteur_type = fields.Selection(
        related='product_tmpl_id.reflecteur_type',
        string="Type Réflecteur ",
        store=True,
    )
    qr_code_uploaded = fields.Image("QR Code", max_width=512, max_height=512)
class CustomerType(models.Model):
    _name = 'customer.type'
    _description = 'Customer Type'

    name = fields.Char(string='Name', required=True)

class PriceType(models.Model):
    _name = 'price.type'
    _description = 'Price Type'

    name = fields.Char(string='Name', required=True)

class PriceTypeUpdate(models.Model):
    _name = 'price.type.update'
    _description = 'Price Type Update'

    name = fields.Char(string='Name', required=True)


class ProductPriceLine(models.Model):
    _name = 'product.price.line'
    _description = 'Product Price Line'

    product_id = fields.Many2one('product.template', string='Produit')
    customer_type_id = fields.Many2one('customer.type', string='Type client', required=True)

    price = fields.Float(string='Prix', required=True)
    intitule=fields.Char(string='Intitulé')
    type_de_prix=fields.Many2one('price.type', string='Type de prix', required=True)


class PriceUpdateWizard(models.TransientModel):
    _name = 'price.update.wizard'
    _description = 'Price Update Wizard'

    customer_type_id = fields.Many2one('customer.type', string='Type de client', required=True)
    price_type_id = fields.Many2one('price.type', string='Type de prix', required=True)
    value = fields.Float(string='Nouveau prix', required=True)

  
    def update_prices(self):
        product_price_line_obj = self.env['product.price.line']
        lines_to_update = product_price_line_obj.search([
            ('customer_type_id', '=', self.customer_type_id.id),
            ('type_de_prix', '=', self.price_type_id.id)
        ])
        for line in lines_to_update:
            line.price = self.value
        return {'type': 'ir.actions.act_window_close'}
