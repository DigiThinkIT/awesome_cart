import frappe
from frappe.utils import update_progress_bar


def execute():
	frappe.reload_doctype("AWC Coupon Item")

	"""Updates Awc Coupon Items to set default values the new
	item_type and item_b_type fields on existing records"""

	# first find all coupon items of which the target item type isn't set
	for citem in frappe.get_all("AWC Coupon Item", filters={"item_type": ""}, as_list=1):
		frappe.db.set_value("AWC Coupon Item", citem[0], "item_type", "Item")

	# next find all coupon items of which the target item_b_type type isn't set
	for citem in frappe.get_all("AWC Coupon Item", filters={"item_b_type": ""}, as_list=1):
		frappe.db.set_value("AWC Coupon Item", citem[0], "item_b_type", "Item")

	frappe.db.commit()
