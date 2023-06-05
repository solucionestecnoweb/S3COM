from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain

class ReportAccountAgedReceivable(models.Model):
    _inherit = "account.aged.receivable"


    @api.model
    def _get_report_name(self):
        return _("Cuentas por Cobrar")


class ReportAccountAgedPayable(models.Model):
    _inherit = "account.aged.payable"


    @api.model
    def _get_report_name(self):
        return _("Cuentas por Pagar")
    



class AccountChartOfAccountReport(models.AbstractModel):
    _inherit = "account.coa.report"


    

    @api.model
    def _get_report_name(self):
        return _("Balance de Comprobación")