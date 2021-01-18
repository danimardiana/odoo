# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models

from dateutil import parser
from datetime import timedelta
from collections import OrderedDict


class Invoice(models.Model):
    _inherit = 'account.move'

    def print_date(self, inv_line):
        month = ' '
        temp = []
        inv_line_unique = []
        for line in list(set(inv_line.mapped('name'))):
            if 'Invoicing period' in line:
                inv_line_unique.append(line)
        if inv_line_unique:
            name = inv_line_unique[0].split(':')
            name = name[-1].split('-')
            start_date = parser.parse(name[0])
            end_date = inv_line_unique[-1].split(':')
            end_date = end_date[-1].split('-')
            end_date = parser.parse(end_date[-1])
            months = OrderedDict(((start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                 range((end_date - start_date).days))

            temp = list(months)
            for i in temp:
                if 'December' not in i:
                    month += i.split('-')[0] + ','
                else:
                    month += ' ' + i + ','
            if len(months) == 1:
                month = list(months)[0]
            # if month and temp:
            #     month += '-' + temp[-1].split('-')[-1] + ' '
            #     month = month.replace(',-' + temp[-1].split('-')[-1], '-' + temp[-1].split('-')[-1])
        return month
