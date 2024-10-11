{
    "name": "MRP Documents Share",
    "summary": """
       add design template to each production operation
    """,
    "author": "Weelite:Fatima AMZIL",
    "website": "https://www.weelite.co",
    "category": "Manufacturing",
    "license": "OPL-1",
    "depends": ["mrp","sale","market_connector",'stock','base'],
    "data": [
        
        "views/mrp_production.xml",
        "views/etiquette_du_produit_fini.xml",
        "views/mrp_order_report.xml",
        "views/custom_report_delivery_document.xml",
        'security/ir.model.access.csv',
      
    ],
    "installable": True,
    "application": False,
    
}
