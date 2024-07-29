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

class CustomerType(models.Model):
    _name = 'customer.type'
    _description = 'Customer Type'

    name = fields.Char(string='Name', required=True)

class PriceType(models.Model):
    _name = 'price.type'
    _description = 'Price Type'

    name = fields.Char(string='Name', required=True)

class ProductPriceLine(models.Model):
    _name = 'product.price.line'
    _description = 'Product Price Line'

    product_id = fields.Many2one('product.template', string='Produit')
    customer_type_id = fields.Many2one('customer.type', string='Type client', required=True)

    price = fields.Float(string='Prix', required=True)
    intitule=fields.Char(string='Intitulé')
    Type_de_prix=fields.Many2one('price.type', string='Type de prix', required=True)


