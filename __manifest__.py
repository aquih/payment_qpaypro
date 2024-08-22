# -*- coding: utf-8 -*-

{
    'name': 'QPayPro Payment Acquirer',
    'category': 'Accounting/Payment',
    'summary': 'Payment Acquirer: QPayPro Implementation',
    'version': '2.0',
    'description': """QPayPro Payment Acquirer""",
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends': ['payment'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_qpaypro_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'uninstall_hook': 'uninstall_hook',
    'license': 'Other OSI approved licence',
}
