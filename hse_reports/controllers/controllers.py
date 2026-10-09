# -*- coding: utf-8 -*-
# from odoo import http


# class HseReports(http.Controller):
#     @http.route('/hse_reports/hse_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hse_reports/hse_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hse_reports.listing', {
#             'root': '/hse_reports/hse_reports',
#             'objects': http.request.env['hse_reports.hse_reports'].search([]),
#         })

#     @http.route('/hse_reports/hse_reports/objects/<model("hse_reports.hse_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hse_reports.object', {
#             'object': obj
#         })

