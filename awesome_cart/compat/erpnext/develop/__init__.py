from __future__ import unicode_literals

__version__ = 'develop'

import frappe

def _customer_total_addresses(customer_name):
	sql = "SELECT COUNT(*) FROM `tabDynamic Link` WHERE \
				parenttype='Address' \
				AND link_doctype='Customer' \
				AND link_name='{}'".format(customer_name)
	return cint(frappe.db.sql(sql, as_list=1)[0][0]);

def _get_list_from_dynlinks(parent_dt, fields, link_dt, link_name, \
	order_by=None, limit=None, limit_start=None):
	if order_by:
		order_by = "ORDER BY {}".format(order_by)

	limit_start = 0 if not limit_start else cint(limit_start)
	limit = cint(limit) if limit else None

	# this is an a quick join to find all dt linked by a dynamic link
	sql = "SELECT {fields} FROM `tab{parent_dt}` a, \
			( \
				SELECT parent FROM `tabDynamic Link` \
					WHERE parenttype='{parent_dt}' \
					AND link_doctype='{link_dt}' \
					AND link_name='{link_name}' \
			) l \
			WHERE a.name = l.parent \
			{order_by} \
			{limit}".format(
				fields = ', '.join(['a.{}'.format(n) for n in fields]),
				parent_dt=parent_dt,
				link_dt=link_dt,
				link_name=link_name,
				order_by=order_by,
				limit="LIMIT {}, {}".format(limit_start, limit) if limit else ''
			)

	return frappe.db.sql(sql, as_dict=1)


def _customer_fetch_addresses(customer_name, start, limit, order_by, fields,
	ignore_permissions=False):
	# NOTE: ignore_permisions unused as we are doing straight sql querying.
	#       Look for a way to obey permissions.
	return _get_list_from_dynlinks(
		"Address",
		fields=fields,
		link_dt="Customer",
		link_name=customer_name,
		order_by=order_by,
		limit_start=start,
		limit=limit
	)
