def migrate(cr, version):
    cr.execute("""
        UPDATE mrp_production 
        SET selected_image_id = NULL 
        WHERE selected_image_id IS NOT NULL
    """) 