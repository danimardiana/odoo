# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from collections import OrderedDict
from datetime import timedelta
from odoo import fields, models, api, _


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    # old SB's code 
    def create_chatter_log(self, budget_line_id, user):
        if budget_line_id.budget_id and budget_line_id.active:
            budget_line_id.budget_id.message_post(body=_(
                """<p>The <a href=# data-oe-model=sale.order.line
            data-oe-id=%d>%s</a> has been created from <a href=# 
                data-oe-model=sale.order data-oe-id=%d>%s</a>, <a href=# data-oe-model=sale.subscription
                data-oe-id=%d>%s</a> <br/> At : %s <br/> Created by <a href=# 
                data-oe-model=res.users
                data-oe-id=%d>%s</a>
                <br/> Upsell Date : %s <br/>
             Upsell Amount : %s
                .</p>""") % (
                                                           budget_line_id.sol_id.id,
                                                           budget_line_id.sol_id.display_name,
                                                           budget_line_id.sol_id.order_id.id,
                                                           budget_line_id.sol_id.order_id.name,
                                                           budget_line_id.subscription_id.id,
                                                           budget_line_id.subscription_id.code,
                                                           fields.Date.today(),
                                                           user.id,
                                                           user.name,
                                                           budget_line_id.start_date if
                                                           budget_line_id.status ==
                                                           'upsell' else 'NO Upsell',
                                                           budget_line_id.price if
                                                           budget_line_id.status ==
                                                           'upsell' else 0.0
                                                       ))
