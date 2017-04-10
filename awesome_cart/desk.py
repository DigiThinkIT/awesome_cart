from __future__ import unicode_literals

import frappe

@frappe.whitelist()
def get_categories(term=""):
	sql = "SELECT tags FROM `tabAWC Item` WHERE tags LIKE '%{0}%' ORDER BY tags ASC".format(term)

	results = frappe.db.sql(sql, as_dict=1)
	tags=[]
	for row in results:
		tags += [tag for tag in (row.get('tags') or '').split(',') if len(tag) > 0 and not (tag in tags)]

	return tags
