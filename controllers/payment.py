# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug
from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class QPayProController(http.Controller):
    _return_url = '/payment/payment_qpaypro/return'

    @http.route(['/payment/payment_qpaypro/return'], type='http', auth='public', csrf=False, save_session=False)
    def qpaypro_return(self, **post):
        """ Process the data returned by QPayPro after redirection.

        :param dict data: The feedback data
        """
        _logger.info('QPayPro: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo()._handle_feedback_data(post, 'qpaypro')

        return request.redirect('/payment/status')