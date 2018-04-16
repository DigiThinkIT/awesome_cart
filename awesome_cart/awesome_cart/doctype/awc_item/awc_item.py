# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.model.document import Document
from awesome_cart.utils import clear_cache

class AWCItem(Document):

	def on_update(self):
		clear_cache()


@frappe.whitelist()
def query_items_with_awc_items(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		select a.product_name as name, i.item_name as description from `tabAWC Item` a, `tabItem` i
			where 
				a.product_name = i.name
				and a.catalog_visible=1
				and (
					a.product_name like %(txt)s
					or i.name like %(txt)s
					or i.item_code like %(txt)s
					or i.item_name like %(txt)s
				)
				and (i.variant_of is null 
				or i.variant_of = '')
			order by
				product_name
			limit %(start)s, %(page_len)s
		""".format(**{
			'key': searchfield
        }), {
            'txt': "%{0}%".format(txt),
            'start': start,
            'page_len': page_len
        })

