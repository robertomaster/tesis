# -*- coding: utf-8 -*-
{
    'name': "tesis",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', "mail", "web_notify"],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sequence.xml',
        'views/views.xml',
        'views/res_paciente.xml',
        'views/prescripcion.xml',
        'views/dispositivos.xml',
        'views/notificaciones.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
