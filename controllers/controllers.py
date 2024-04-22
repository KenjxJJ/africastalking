# -*- coding: utf-8 -*-
# from odoo import http


# class OdooAfricastalking(http.Controller):
#     @http.route('/odoo_africastalking/odoo_africastalking/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo_africastalking/odoo_africastalking/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo_africastalking.listing', {
#             'root': '/odoo_africastalking/odoo_africastalking',
#             'objects': http.request.env['odoo_africastalking.odoo_africastalking'].search([]),
#         })

#     @http.route('/odoo_africastalking/odoo_africastalking/objects/<model("odoo_africastalking.odoo_africastalking"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo_africastalking.object', {
#             'object': obj
#         })
