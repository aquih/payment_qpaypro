# coding: utf-8
import logging
import json

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_qpaypro.controllers.payment import QPayProController
from odoo.tools.float_utils import float_compare
from odoo.http import request

import requests

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'qpaypro':
            return res
        
        return_url = urls.url_join(self.acquirer_id.get_base_url(), QPayProController._return_url)

        data = {
            'x_login': self.acquirer_id.qpaypro_llave_publica,
            'x_api_key': self.acquirer_id.qpaypro_llave_privada,
            'x_amount': processing_values['amount'],
            'x_currency_code': self.currency_id.name,
            'x_first_name': self.partner_id.name,
            'x_last_name': '-',
            'x_phone': self.partner_id.phone or '-',
            'x_ship_to_address': (self.partner_id.street or '-') + (self.partner_id.street2 or '-'),
            'x_ship_to_city': self.partner_id.city or '-',
            'x_ship_to_country': self.partner_id.country_id.name or '-',
            'x_ship_to_state': self.partner_id.state_id.name or '-',
            'x_ship_to_zip': self.partner_id.zip or '-',
            'x_ship_to_phone': self.partner_id.phone or '-',
            'x_company': self.partner_id.vat or '-',
            'x_address': (self.partner_id.street or '-') + (self.partner_id.street2 or '-'),
            'x_city': self.partner_id.city or '-',
            'x_country': self.partner_id.country_id.name or '-',
            'x_state': self.partner_id.state_id.name or '-',
            'x_freight': '',
            'x_zip': self.partner_id.zip or '-',
            'x_email': self.partner_id.email or '-',
            'x_description': self.reference,
            'x_reference': self.reference,
            'x_invoice_num': self.reference,
            'x_url_cancel': return_url,
            'x_relay_url': return_url,
            'x_type': 'AUTH_ONLY',
            'x_method': 'CC',
            'custom_fields': '{}',
            'x_visacuotas': 'si',
            'products': '[]',
            'taxes': '0',
            'http_origin': self.acquirer_id.get_base_url(),
            'origen': 'PLUGIN',
        }
        
        _logger.warning(json.dumps(data, indent=4))
        _logger.warning(self.state)

        token_url = 'https://sandboxpayments.qpaypro.com/checkout/register_transaction_store'
        if self.acquirer_id.state == 'enabled':
            token_url = 'https://payments.qpaypro.com/checkout/register_transaction_store'
        _logger.warning(token_url)
        
        r = requests.post(token_url, json=data)
        resultado = r.json()
        _logger.warning(json.dumps(resultado, indent=4))
        
        rendering_values = {
            'api_url': self.acquirer_id._qpaypro_get_api_url(),
            'qpaypro_token': resultado['data']['token'],
        }
        return rendering_values
        
    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'qpaypro':
            return tx
        
        reference = data.get('x_invoice_num', '')
        if not reference:
            error_msg = _('QPayPro: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference), ('provider', '=', 'qpaypro')])
        _logger.info(tx)

        if not tx or len(tx) > 1:
            error_msg = _('QPayPro: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple orders found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'qpaypro':
            return
        
        reference = data.get('x_invoice_num', '')
        
        self.acquirer_reference = reference
        status_code = data.get('x_response_status', '3')
        if status_code == '1':
            self._set_done()
        else:
            error = 'QPayPro: error '+data.get('x_response_text')
            _logger.info(error)
            self._set_error(_("Your payment was refused (code %s). Please try again.", status_code))
