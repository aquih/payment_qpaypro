# coding: utf-8
import logging

from odoo import api, fields, models, _

from odoo.addons.payment_qpaypro import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'
    
    code = fields.Selection(selection_add=[('qpaypro', 'QPayPro')], ondelete={'qpaypro': 'set default'})
    qpaypro_llave_publica = fields.Char('Llave Pública', required_if_provider='qpaypro', groups='base.group_user')
    qpaypro_llave_privada = fields.Char('Llave Privada', required_if_provider='qpaypro', groups='base.group_user')

    def _qpaypro_get_api_url(self):
        self.ensure_one()
        if self.state == 'enabled':
            return "https://payments.qpaypro.com/checkout/store"
        else:
            return "https://sandboxpayments.qpaypro.com/checkout/store"

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'qpaypro':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
