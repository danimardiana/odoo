# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models

from dateutil import parser
from dateutil import relativedelta
from datetime import datetime, timedelta
from collections import OrderedDict


class Invoice(models.Model):
    _inherit = 'account.move'

    def unique_list(self, l):
        ulist = []
        [ulist.append(x) for x in l if x not in ulist]
        return ulist

    def print_date(self, inv_line):
        month = ' '
        for line in inv_line:
            if line.name:
                name = line.name.split(':')
                name = name[-1].split('-')
                start_date = parser.parse(name[0])
                end_date = parser.parse(name[-1])
                months = OrderedDict(((start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                     range((end_date - start_date).days))
                month = ''
                temp = list(months)
                for i in temp:
                    if 'December' not in i:
                        month += i.split('-')[0] + ','
                    else:
                        month += ' ' + i + ','
                month += '-' + temp[-1].split('-')[-1]
        return month
