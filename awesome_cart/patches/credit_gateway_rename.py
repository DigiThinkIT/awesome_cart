import frappe
from frappe.utils import update_progress_bar


def execute():
	if frappe.db.exists("Payment Gateway", "Credit Gateway Settings"):
		frappe.rename_doc("Payment Gateway", "Credit Gateway Settings", "Credit Gateway", force=True)

	frappe.db.commit()
