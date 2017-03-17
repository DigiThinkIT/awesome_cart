from __future__ import unicode_literals
import frappe
from frappe import throw, _

from awesome_cart.compat.erpnext.shopping_cart import get_cart_quotation, apply_cart_settings

def convert_quotation_to_sales_order(quotation):
    quotation.company = frappe.db.get_value("Shopping Cart Settings", None, "company")
    for fieldname in ["customer_address", "shipping_address_name"]:
        if not quotation.get(fieldname):
            throw(_("{0} is required").format(quotation.meta.get_label(fieldname)))

    quotation.flags.ignore_permissions = True
    quotation.submit()

    if quotation.lead:
        # company used to create customer accounts
        frappe.defaults.set_user_default("company", quotation.company)

    from erpnext.selling.doctype.quotation.quotation import _make_sales_order
    sales_order = frappe.get_doc(_make_sales_order(quotation.name, ignore_permissions=True))
    for item in sales_order.get("items"):
        item.reserved_warehouse = frappe.db.get_value("Item", item.item_code, "website_warehouse") or None

    sales_order.flags.ignore_permissions = True
    sales_order.insert()
    sales_order.submit()
    return sales_order
