{
    'name': 'Venezuela - Account Reports',
    'version': '15.0.1.0',
    'summary': '',
    'description': '',
    'category': 'Accounting/Accounting',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'l10n_ve_base',
        'l10n_ve_account',
        'l10n_ve_account_tax_amount',
        'l10n_ve_account_sequence_number',
        'l10n_ve_currency_rate',
        'l10n_ve_igtf',
    ],
    'data': [
        'report/paperformat.xml',
        'report/ir_action_report.xml',
        'views/report_account_invoice.xml',
        'views/report_account_invoice_credit.xml',
        'views/report_account_invoice_debit.xml',
        'views/report_account_invoice_delivery_note.xml',
        'views/account_move_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'l10n_ve_account_reports/static/src/css/style.css',
        ],
    },
    'installable': True,
    'auto_install': False
}
