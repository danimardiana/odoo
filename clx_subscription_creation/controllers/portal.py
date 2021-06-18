# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii

from datetime import date

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper

# from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.osv import expression


def get_records_pager(ids, current):
    if current.id in ids and (hasattr(current, "website_url") or hasattr(current, "access_url")):
        attr_name = "access_url" if hasattr(current, "access_url") else "website_url"
        idx = ids.index(current.id)
        return {
            "prev_record": idx != 0 and getattr(current.browse(ids[idx - 1]), attr_name),
            "next_record": idx < len(ids) - 1 and getattr(current.browse(ids[idx + 1]), attr_name),
        }
    return {}

# These fake objects created to avoid the real lines creation  in the DB just for report generation
class FakeSaleOrderLine:
    def __init__(self, sol, ratio):
        self.order_id = sol.order_id
        self.product_id = sol.product_id
        self.price_unit = sol.price_unit * ratio / 100
        self.name = sol.name
        self.partner_id = sol.product_id
        self.prorate_amount = sol.prorate_amount * ratio / 100
        self.display_type = sol.display_type
        self.product_template_id = sol.product_template_id
        self.product_type = sol.product_type
        self.discount = 0
        self._grouping_name_calc = sol.env["sale.order.line"]._grouping_name_calc


class FakeSaleOrder:
    def append_sale_order_line(self, line, ratio):
        self.order_line.append(FakeSaleOrderLine(line, ratio))

    def __init__(self, so, partner_id):
        self.partner_id = partner_id
        self.partner_invoice_id = so.partner_invoice_id
        self._grouping_wrapper = so.env["sale.order"]._grouping_wrapper
        self.contract_start_date = so.contract_start_date
        self.order_line = []
        self.display_management_fee = False
        self.signature = False
        self.pricelist_id = so.pricelist_id
        # self.money_formatting = so.money_formatting



class CustomerPortal(CustomerPortal):
    @http.route(["/my/orders/<int:order_id>/accept"], type="json", auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get("access_token")
        try:
            order_sudo = self._document_check_access("sale.order", order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {"error": _("Invalid order.")}

        if not order_sudo.has_to_be_signed():
            return {"error": _("The order is not in a state requiring customer signature.")}
        if not signature:
            return {"error": _("Signature is missing.")}

        try:
            order_sudo.write(
                {
                    "signed_by": name,
                    "signed_on": fields.Datetime.now(),
                    "signature": signature,
                }
            )
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {"error": _("Invalid signature data.")}

        if not order_sudo.has_to_be_paid():
            order_sudo.action_confirm()
            order_sudo._send_order_confirmation_mail()

        # pdf = request.env.ref('sale.action_report_saleorder').sudo(
        # ).render_qweb_pdf([order_sudo.id])[0]

        # removin additional messaging
        # _message_post_helper(
        #     'sale.order', order_sudo.id, _('Order signed by %s') % (name,),
        #     attachments=[('%s.pdf' % order_sudo.name, pdf)],
        #     **({'token': access_token} if access_token else {}))

        query_string = "&message=sign_ok"
        if order_sudo.has_to_be_paid(True):
            query_string += "#allow_payment=yes"
        return {
            "force_refresh": True,
            "redirect_url": order_sudo.get_portal_url(query_string=query_string),
        }

    @http.route(["/my/orders/<int:order_id>"], type="http", auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            order_sudo = self._document_check_access("sale.order", order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")

        communities = {}

        for so_line in order_sudo.order_line:
            if order_sudo.is_co_op and len(so_line.co_op_sale_order_line_partner_ids) > 0:
                for community in so_line.co_op_sale_order_line_partner_ids:
                    if community.partner_id.id not in communities:
                        fake_order = FakeSaleOrder(order_sudo, community.partner_id)
                        communities[community.partner_id.id] = fake_order
                    communities[community.partner_id.id].append_sale_order_line(so_line, community.ratio)

        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=order_sudo, report_type=report_type, report_ref="sale.action_report_saleorder", download=download
            )

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        if order_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get("view_quote_%s" % order_sudo.id)
            if isinstance(session_obj_date, date):
                session_obj_date = session_obj_date.isoformat()
            if session_obj_date != now and request.env.user.share and access_token:
                request.session["view_quote_%s" % order_sudo.id] = now
                body = _("Quotation viewed by customer %s") % order_sudo.partner_id.name
                _message_post_helper(
                    "sale.order",
                    order_sudo.id,
                    body,
                    token=order_sudo.access_token,
                    message_type="notification",
                    subtype="mail.mt_note",
                    partner_ids=order_sudo.user_id.sudo().partner_id.ids,
                )

        values = {
            "sale_order": order_sudo,
            "message": message,
            "token": access_token,
            "return_url": "/shop/payment/validate",
            "bootstrap_formatting": True,
            "partner_id": order_sudo.partner_id.id,
            "report_type": "html",
            "action": order_sudo._get_portal_return_action(),
            "communities": list(communities.values()),
        }
        if order_sudo.company_id:
            values["res_company"] = order_sudo.company_id

        params = request.env["ir.config_parameter"].sudo()
        setup_fee_product = int(params.get_param("contract_management_fee_product", False)) or False
        values["setup_fee_product"] = setup_fee_product

        if order_sudo.has_to_be_paid():
            domain = expression.AND(
                [
                    ["&", ("state", "in", ["enabled", "test"]), ("company_id", "=", order_sudo.company_id.id)],
                    ["|", ("country_ids", "=", False), ("country_ids", "in", [order_sudo.partner_id.country_id.id])],
                ]
            )
            acquirers = request.env["payment.acquirer"].sudo().search(domain)

            values["acquirers"] = acquirers.filtered(
                lambda acq: (acq.payment_flow == "form" and acq.view_template_id)
                or (acq.payment_flow == "s2s" and acq.registration_view_template_id)
            )
            values["pms"] = request.env["payment.token"].search([("partner_id", "=", order_sudo.partner_id.id)])
            values["acq_extra_fees"] = acquirers.get_acquirer_extra_fees(
                order_sudo.amount_total, order_sudo.currency_id, order_sudo.partner_id.country_id.id
            )

        if order_sudo.state in ("draft", "sent", "cancel"):
            history = request.session.get("my_quotations_history", [])
        else:
            history = request.session.get("my_orders_history", [])
        values.update(get_records_pager(history, order_sudo))

        return request.render("sale.sale_order_portal_template", values)
