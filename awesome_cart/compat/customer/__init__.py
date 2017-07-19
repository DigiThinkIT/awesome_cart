from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.shopping_cart import cart
from awesome_cart.compat.shopping_cart import get_cart_quotation
from awesome_cart import compat, session

class AddressNotFoundError(compat.CompatException):
	def __init__(address_info):
		super(AddressNotFoundError, this).__init("Address was not found: {}".format(address_info))

def total_addresses(customer_name):
	return compat.erpnext._customer_total_addresses(customer_name)

def fetch_addresses(customer_name, start, limit, order_by, fields=[
	"address_title", "address_type", "address_line1",
	"address_line2", "city", "country", "state", "county", "pincode",
	"is_primary_address", "is_shipping_address", "name"],
	ignore_permissions=False):

	return compat.erpnext._customer_fetch_addresses(
		customer_name=customer_name,
		start=start,
		limit=limit if limit else 10,
		order_by=order_by,
		fields=fields,
		ignore_permissions=ignore_permissions)

def delete_address(customer_name, address_id, ignore_permissions=False):

	if not address_id:
		raise compat.ArgumentMissingError('address_id')

	address = frappe.get_doc("Address", address_id)

	# sanity check to make sure we only delete addresses which belong
	# to the customer in session
	if address and address.customer == customer_name:
		frappe.delete_doc("Address", address_id, ignore_permissions=ignore_permissions)
		return True

	raise AddressNotFoundError(address_id)

def get_current_customer():
	session_user = frappe.get_user()
	if session_user.name == "Guest":
		return None

	awc_session = session.get_awc_session()
	party = None
	if awc_session.get("selected_customer"):
		party = frappe.get_doc("Customer", awc_session["selected_customer"])

	quotation = get_cart_quotation(party=party)["doc"]
	customer = frappe.get_doc("Customer", quotation.customer)
	return customer
