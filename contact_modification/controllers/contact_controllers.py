# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ContactContoller(http.Controller):
    @http.route(["/subscriberlist/"], type="json", auth="none", methods=["POST"])
    def get_subscribed_clients(self, access_token):
        params = request.env["ir.config_parameter"].sudo()
        access_token_settings = params.get_param("api_token", False)

        if access_token != access_token_settings:
            return {"status": 404, "response": {"error": "Access Token is wrong"}}

        subscription_query = """select sub.id,
                                sub.partner_id,
                                sub.is_active 
                                from (select ss.id,
                                             ss.partner_id,
                                             ss.is_active 
                                      from sale_subscription ss
                                      union
                                      select ss.id,
                                             coop.partner_id,
                                             ss.is_active 
                                      from co_op_subscription_partner coop
                                      inner join sale_subscription ss on ss.id = coop.subscription_id
                                      ) as sub
                                order by sub.id;"""
        http.request._cr.execute(subscription_query)
        subscription_result = http.request._cr.fetchall()

        subscriber_map = {}
        subscriber_ids = []
        odoo_companies = []

        for company in subscription_result:
            if not company[0] in subscriber_map:
                subscriber_map[company[0]] = company[1]
                company_id_str = str(company[0])
                subscriber_ids.append(company_id_str)
            else:
                if company[1]:
                    subscriber_map[company[0]] = True

        id_tuple = tuple(subscriber_ids)
        company_query = """ 
                        SELECT rp.id,
                               rp.name,
                               rp.company_type,
                               rp.vertical,
                               rp.street,
                               rp.street2,
                               rp.city,
                               rcs.code,
                               rp.zip,
                               rp.website
                        FROM res_partner rp
                        LEFT JOIN res_country_state rcs on rcs.id = rp.state_id
                        WHERE rp.id IN {}; """.format(
            id_tuple
        )
        http.request._cr.execute(company_query)
        company_result = http.request._cr.fetchall()

        for record in company_result:
            location = (
                str(record[4])
                + " "
                + str(record[5])
                + " "
                + str(record[6])
                + ", "
                + str(record[7])
                + " "
                + str(record[8])
            )
            company_obj = {
                "company_name": record[1],
                "vertical": record[3],
                "location": location,
                "is_active": subscriber_map[record[0]],
                "item_id": record[0],
                "homepage_urls": record[9],
            }
            odoo_companies.append(company_obj)

        return {
            "status": 200,
            "response": {"data": odoo_companies},
        }

    @http.route(["/companies/<string:company>"], type="json", auth="none", csrf=False, methods=["POST"])
    def get_companies(self, company):
        if len(company) < 3:
            return {"status": 404, "response": {"error": "Company name too short"}}

        if "company_type" not in request.jsonrequest:
            return {"status": 404, "response": {"error": "company_type not set"}}

        company_type = "company"

        if request.jsonrequest["company_type"] in ["person", "owner", "company", "management"]:
            company_type = request.jsonrequest["company_type"]

        limit = 10

        if "limit" in request.jsonrequest:
            limit = request.jsonrequest["limit"]

        company_query = """ 
                SELECT id, name, company_type, vertical
                FROM res_partner
                WHERE LOWER(name) LIKE LOWER('%{company}%') and company_type='{company_type}' LIMIT {limit}; """.format(
            company=company, company_type=company_type, limit=limit
        )
        cr = request.registry.cursor()
        cr.execute(company_query)
        company_result = cr.fetchall()
        odoo_companies = list(
            map(lambda d: {"id": d[0], "name": d[1], "company_type": d[2], "vertical": d[3]}, company_result)
        )

        return {
            "status": 200,
            "response": {"data": odoo_companies},
        }
