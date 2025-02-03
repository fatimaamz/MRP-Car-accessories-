def migrate(cr, version):
    # Set all existing selected_image_id to NULL before changing the model
    cr.execute("""
        UPDATE mrp_production 
        SET selected_image_id = NULL 
        WHERE selected_image_id IS NOT NULL
    """) 