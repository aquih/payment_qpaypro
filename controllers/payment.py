# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug
from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class QPayProController(http.Controller):
    _return_url = '/payment/qpaypro/return'

    @http.route(['/payment/qpaypro/return'], type='http', auth='public', csrf=False, save_session=False)
    def qpaypro_return(self, **data):
        """ Process the data returned by QPayPro after redirection.

        :param dict data: The feedback data
        """
        if data:
            _logger.info('QPayPro: entering form_feedback with post data %s', pprint.pformat(data))  # debug
            request.env['payment.transaction'].sudo()._handle_feedback_data('qpaypro', data)
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('qpaypro', data)
            tx_sudo._handle_notification_data('qpaypro', data)

        return request.redirect('/payment/status')