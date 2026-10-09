# -*- coding: utf-8 -*-
# from odoo import http


# class HseMeeting(http.Controller):
#     @http.route('/hse_meeting/hse_meeting', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hse_meeting/hse_meeting/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hse_meeting.listing', {
#             'root': '/hse_meeting/hse_meeting',
#             'objects': http.request.env['hse_meeting.hse_meeting'].search([]),
#         })

#     @http.route('/hse_meeting/hse_meeting/objects/<model("hse_meeting.hse_meeting"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hse_meeting.object', {
#             'object': obj
#         })

