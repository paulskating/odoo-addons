# _*_ coding: utf-8 _*_
{
    'name': "mrp_insufficient_material",
    'version': '1.0',
    'depends': ["mrp", "product_qty_in_stock"],
    'author': "糖葫芦(39181819@qq.com)",
    'category': '',
    'description': """

    """,
    'data': ["data/menu.xml",
             "data/report_paperformat.xml",
             "wizards/report_product_insufficient_wizard_view.xml",
             "wizards/report_production_insufficient_wizard_view.xml",
             "templates/report_product_insufficient_template.xml",
             "templates/report_production_insufficient_template.xml",
             "report/report.xml"],
    'demo': [],
}
