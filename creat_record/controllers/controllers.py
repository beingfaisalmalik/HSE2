# -*- coding: utf-8 -*-
# from odoo import http


# class CreatRecord(http.Controller):
#     @http.route('/creat_record/creat_record', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/creat_record/creat_record/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('creat_record.listing', {
#             'root': '/creat_record/creat_record',
#             'objects': http.request.env['creat_record.creat_record'].search([]),
#         })

#     @http.route('/creat_record/creat_record/objects/<model("creat_record.creat_record"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('creat_record.object', {
#             'object': obj
#         })

