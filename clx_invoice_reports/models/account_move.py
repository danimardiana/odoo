# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models

from dateutil import parser
from dateutil import relativedelta


class Invoice(models.Model):
    _inherit = 'account.move'

    def unique_list(self, l):
        ulist = []
        [ulist.append(x) for x in l if x not in ulist]
        return ulist

    def print_date(self, inv_line):
        month = ' '
        start_date = False
        for line in inv_line:
            if line.name:
                name = line.name.split(':')
                name = name[-1].split('-')
                start_date = parser.parse(name[0])
                end_date = parser.parse(name[-1])
                month_diff = relativedelta.relativedelta(end_date, start_date)
                for i in range(0, month_diff.months + 1):
                    temp_start_date = start_date + relativedelta.relativedelta(months=1)
                    if start_date.year != temp_start_date.year:
                        month = start_date.strftime('%B') + ' ' + start_date.strftime('%Y')
                    else:
                        month += ' ' + start_date.strftime('%B') + ','
                    start_date = temp_start_date
                    last_date = start_date
                start_date = False
        month += '-' + str(last_date.year)
        unique_string = ' '.join(self.unique_list(month.split()))
        return unique_string
