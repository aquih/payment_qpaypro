# coding: utf-8
import logging
import json

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.payment_qpaypro.controllers.payment import QPayProController

import requests

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        logging.warning(processing_values)
        if processing_values['provider_code'] != 'qpaypro':
            return res
        
        return_url = urls.url_join(self.provider_id.get_base_url(), QPayProController._return_url)

        data = {
            'x_login': self.provider_id.qpaypro_llave_publica,
            'x_api_key': self.provider_id.qpaypro_llave_privada,
            'x_amount': processing_values['amount'],
            'x_currency_code': self.currency_id.name,
            'x_first_name': self.partner_id.name.split(maxsplit=1)[0],
            'x_last_name': self.partner_id.name.split(maxsplit=1)[-1],
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
            'custom_fields': {'reference': self.reference, 'amount': processing_values['amount']},
            'x_visacuotas': 'si' if processing_values['amount'] >= 1000 else 'no',
            'products': [[self.company_id.name, self.company_id.name, '', 1, processing_values['amount'], processing_values['amount']]],
            'taxes': '0',
            'http_origin': self.provider_id.get_base_url(),
            'origen': 'PLUGIN',
        }
        
        _logger.warning(json.dumps(data, indent=4))
        _logger.warning(self.state)

        token_url = 'https://sandboxpayments.qpaypro.com/checkout/register_transaction_store'
        if self.provider_id.state == 'enabled':
            token_url = 'https://payments.qpaypro.com/checkout/register_transaction_store'
        _logger.warning(token_url)
        
        r = requests.post(token_url, json=data)
        resultado = r.json()
        _logger.warning(json.dumps(resultado, indent=4))
        
        rendering_values = {
            'api_url': self.provider_id._qpaypro_get_api_url(),
            'qpaypro_token': resultado['data']['token'],
        }
        return rendering_values
        
    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'qpaypro':
            return tx
        
        reference = notification_data.get('reference', '')
        if not reference:
            error_msg = _('QPayPro: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'qpaypro')])
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

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'qpaypro':
            return
        
        self.provider_reference = notification_data.get('reference', '')

        payment_method = self.env['payment.method']._get_from_code(
            'qpaypro'
        )
        _logger.info(payment_method)
        self.payment_method_id = payment_method or self.payment_method_id

        status_code = notification_data.get('x_response_status', '3')
        if status_code == '1':
            self._set_done()
        else:
            error = 'QPayPro: error '+data.get('x_response_text')
            _logger.info(error)
            self._set_error(_("Your payment was refused (code %s). Please try again.", status_code))
