# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from awesome_cart.session import set_cache
from awesome_cart.utils import clear_cache

class AWCItem(Document):

	def on_update(self):
		item_code = frappe.db.get_value("Item", self.product_name, "item_code")

		# general cache clear
		clear_cache()

		# secondary flagging for cache invalidation in case redis isn't running(frappe.local.cache storage)
		set_cache("awc-item-invalidate-cache-{}".format(item_code), True)
		set_cache("awc-catalog-invalidate", True)

		# figure out all products that might be refering to this item and flag them as invalid cache so we regen
		related_parents = frappe.db.get_list("AWC Item Recomendation",
			filters={"item_name": self.product_name, "parenttype": "AWC Item"},
			fields=["parent"])
		for row in related_parents:
			if row.get("parent"):
				set_cache("awc-item-invalidate-cache-{}".format(row.get("parent")), True)


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

