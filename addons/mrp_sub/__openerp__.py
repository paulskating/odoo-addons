# _*_ coding: utf-8 _*_
{
    'name': "mrp subcontract",
    'version': '1.0',
    'depends': ["mail", "mrp", "purchase"],
    'author': "糖葫芦(39181819@qq.com)",
    'category': '',
    'description': """
    
    """,
    'data': ["data/sequence.xml",
             "data/mrp_route.xml",
             "data/warehouse.xml",
             "views/stock_move_view.xml",
             "data/stock_picking.xml",
             "wizards/create_out_picking_wizard_views.xml",
             "wizards/change_material_product_wizard_view.xml",
             "views/mrp_subcontract_views.xml",
             "views/procurement_order_view.xml"],
    'demo': [],
    'application': True
}
