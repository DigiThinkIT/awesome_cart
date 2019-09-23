from __future__ import unicode_literals

import json
import traceback
import frappe

from frappe.utils.password import check_password
from frappe.utils import get_url

from erpnext.shopping_cart import cart
from erpnext.accounts.doctype.payment_request import payment_request

from . import embed
from compat.erpnext import get_address_display
from .data import \
	map_address_widget_to_address_doctype, \
	get_doctype_next_series, \
	transfer_quotation_to_user, \
	find_user_customer

from .dbug import deprecated, log, get_trace


ADDRESS_FIELDS = ['address_id', 'address_title', \
	'address_1', 'address_2', 'country', \
	'city', 'state', 'zip', 'phone' ]

def is_logged_in():
	log("Are we still using this method?\n{0}".format(get_trace()))
	session_user = frappe.get_user()

	if session_user.name == "Guest":
		return False

	return True

def _create_customer_address(fields, customer, prefix, address_type='Billing'):
	log("Are we still using this method?\n{0}".format(get_trace()))

	address = map_address_widget_to_address_doctype(fields, prefix)
	# set the doctype field so we can insert this record
	address['doctype'] = "Address"

	# set the customer name and other meta
	address['address_title'] = get_doctype_next_series('Address', "%s-%s" % (fields[prefix+"address_title"], address_type))
	address['address_type'] = address_type
	address['customer'] = customer.name
	address['customer_name'] = customer.customer_name

	address_doc = frappe.get_doc(address)
	#address_doc.insert()

	return address_doc

@frappe.whitelist(allow_guest=True, xss_safe=True)
def login(email, password):
	result = dict(
		success=False,
		msg="Internal Unhandled Error"
	)

	log("Are we still using this method?\n{0}".format(get_trace()))

	try:

		quotation = cart.get_cart_quotation()["doc"]

		user_doc = check_password(email, password)
		frappe.local.login_manager.login_as(email)
		frappe.set_user(email)
		user = frappe.get_doc("User", email)

		# move quotation to logged in user
		transfer_quotation_to_user(quotation, user)

		result["success"] = True
		result["msg"] = ""
		result["user"] = {
			"full_name": user.full_name,
			"name": user.name
		}
	except frappe.AuthenticationError as ex:
		result["success"] = False
		result["msg"] = str(ex)

	return result

@frappe.whitelist(allow_guest=False, xss_safe=True)
def checkout(form):
	log("Are we still using this method?\n{0}".format(get_trace()))

	result = {
		"success": False,
		"msg": "Not Implemented",
		"errors": {}
	}

	try:
		form = json.loads(form)
	except:
		result["msg"] = "Invalid data"
		return result

	billing = form.get("billing", {})
	shipping = form.get("shipping", {})
	session_user = frappe.get_user()
	customer = None
	user = frappe.get_doc("User", session_user.name)
	form["user"] = {
		"email": user.email
	}
	result['form'] = form	# set form back to browser to update any ids as neccessary


	gateway = None

	try:
		quotation = cart.get_cart_quotation()
		quote = quotation["doc"]
		gateway = embed.get_gateway_module(billing.get("gateway", None))
		customer = frappe.get_doc("Customer", quote.customer)
	except:
		result["success"] = False
		result["msg"] = "Internal Error"
		result["exception"] = traceback.format_exc()

	try:
		if gateway:

			bill_address = None
			bill_address_insert = False
			ship_address = None
			ship_address_insert = False

			# lets extract billing address if one was entered
			if not billing['fields'].get('bill_address_id', False):
				bill_address = {
					k: billing['fields'].get(k, None) \
					for k in ["bill_%s" % j for j in ADDRESS_FIELDS]
				}
				bill_address = _create_customer_address(bill_address, customer, 'bill_')
				bill_address.flags.ignore_permissions = True
				bill_address_insert = True
			else:
				bill_address = frappe.get_doc('Address', billing['fields']['bill_address_id'])

			if not shipping['fields'].get('ship_address_id', False):
				ship_address = {
					k: shipping['fields'].get(k, None) \
					for k in ["ship_%s" % j for j in ADDRESS_FIELDS]
				}
				ship_address = _create_customer_address(ship_address, customer, 'ship_')
				ship_address.flags.ignore_permissions = True
				ship_address_insert = True
			else:
				ship_address = frappe.get_doc('Address', shipping['fields']['ship_address_id'])

			# setup transaction
			transaction = create_transaction(quote.grand_total, quote.currency)
			transaction.email = user.email

			stored_payment = None
			if form.get("stored_payment", False):
				stored_payment = None # update with new doctype

			try:
				success, msg = gateway.process(transaction, form, stored_payment, bill_address, ship_address)
				if success:
					result["success"] = True

					# on success insert new addresses
					if bill_address_insert:
						bill_address.insert()
						billing['fields']['bill_address_id'] = bill_address.name

					if ship_address_insert:
						# regenerate title since erpnext uses
						# title to generate id(name) in case
						# billing address uses same title
						ship_address.address_title = get_doctype_next_series('Address', "%s-%s" % (shipping['fields']['ship_address_title'], 'Shipping'))

						ship_address.insert()
						shipping['fields']['ship_address_id'] = ship_address.name
					# apply addresses to quotation
					quote.shipping_address_name = ship_address.name
					quote.shipping_address = get_address_display(ship_address.as_dict())
					quote.customer_address = bill_address.name
					quote.address_display = get_address_display(bill_address.as_dict())
					quote.flags.ignore_permissions = True
					quote.save()

					# now we'll submit quotation, create sales order,
					# create payment request and fullfill it
					so_name = cart.place_order() # submit quotation and create so
					result["so_name"] = so_name

					# lets now create a payment request and fullfill it immediately
					preq = payment_request.make_payment_request(dt="Sales Order", dn=so_name, submit_doc=1, return_doc=1)

					if preq:
						gdoc = gateway.get_gateway()
						adoc = gateway.get_bank_account()
						gadoc = gateway.get_account()

						preq.payment_gateway = gdoc.name
						preq.payment_account = adoc.name
						preq.payment_gateway_account = gadoc.name

						preq.flags.ignore_validate_update_after_submit = 1
						preq.flags.ignore_permissions = True
						preq.save()

						payment_entry = preq.run_method("set_as_paid")

						transaction.log(json.dumps(sanitize_checkout_form(form), indent=4))
						transaction.reference_doctype = "Payment Request"
						transaction.reference_docname = preq.name
						transaction.gateway = gdoc.name
						transaction.save()

						# find invoice
						inv_item = frappe.get_list("Sales Invoice Item", fields=["parent"], filters={"sales_order": so_name})[0]
						result["inv_name"] = inv_item.get("parent")

						frappe.session['awc_success_inv_name'] = inv_item.get("parent")
						frappe.session['awc_success_so_name'] = so_name
						frappe.session['awc_success_email'] = user.email


				else:
					result["success"] = False
					result["msg"] = msg
			except:
				transaction.log(json.dumps(sanitize_checkout_form(form), indent=4))
				transaction.status = "Failed"
				transaction.log(traceback.format_exc() + "\n---\n")
				transaction.save()

				result["success"] = False
				result["msg"] = 'Internal Error'
				result["exception"] = traceback.format_exc()
				raise
	except:
		result["success"] = False
		if not result.get('msg'):
			result['msg'] = 'Internal Error'

		if not result.get('exception'):
			result['exception'] = traceback.format_exc()

	return result

@frappe.whitelist(allow_guest=True, xss_safe=True)
def register(email, password, password_check, first_name, last_name):
	log("Are we still using this method?\n{0}".format(get_trace()))

	result = dict(
		success=False,
		msg="Unhandled Error"
	)

	guest_user = frappe.get_user()
	user = frappe.get_doc("User", guest_user.name)

	quotation = cart.get_cart_quotation()["doc"]

	if user:
		if user.email[-12:] == "@guest.local":
			user.email = email
			user.first_name = first_name
			user.last_name = last_name
			user.new_password = password
			user.flags.ignore_permissions = True
			user.save()

			old_name = user.name

			frappe.rename_doc("User", old_name, email, ignore_permissions=True)
			user.name = email
			user.owner = user.name
			user.save()

			frappe.local.login_manager.login_as(email)
			frappe.set_user(email)

			customer = None
			contact = frappe.get_doc("Contact", {
				"user": email
			})

			if contact:
				contact.first_name = first_name
				contact.last_name = last_name
				contact.email_id = email
				contact.flags.ignore_permissions = True
				contact.save()

				frappe.rename_doc("Contact", contact.name, email, ignore_permissions=True)
				contact.name = email

				customer = frappe.get_doc("Customer", contact.customer)

				if customer and customer.name.startswith("Guest"):
					customer.full_name = "%s %s" % (first_name, last_name)

					customer.flags.ignore_permissions = True
					customer.save()

					customer_next = get_doctype_next_series("Customer", customer.full_name)
					frappe.rename_doc("Customer", customer.name, customer_next, ignore_permissions=True)
					customer.name = customer_next

			# move quotation to logged in user
			transfer_quotation_to_user(quotation, user, customer=customer, contact=contact)

			result["success"] = True
			result["msg"] = ""
			result["user"] = {
				"full_name": user.full_name,
				"name": user.name
			}

		else:
			result["msg"] = "User is not a guest: %s" % user.email
	else:
		result["msg"] = "Internal Error, could not fetch user: %s" % guest_user.name

	return result

@frappe.whitelist(allow_guest=True, xss_safe=True)
def start_checkout(amount, currency="USD", date=None):
	log("Are we still using this method?\n{0}".format(get_trace()))

	validate_transaction_currency(currency)

	if not isinstance(data, basestring):
		date = frappe.as_json(data or "{}")

	jdata = json.loads(data)

	if jdata.get("doctype") and jdata.get("docname"):
		reference_doctype = jdata.get("doctype")
		reference_docname = jdata.get("docname")
		reference_doc = frappe.get_doc(reference_doctype, reference_docname)

		if reference_doctype == "Payment Request":
			if reference_doc.status not in ["Draft", "Initiated"]:
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = get_url(
				"/orders/{0}".format(reference_doc.reference_name))
				return

		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = get_url("/gateway?name={0}&source={1}".format(reference_docname, reference_doctype))

def sanitize_checkout_form(form):
	log("Are we still using this method?\n{0}".format(get_trace()))
	if "billing" in form:
		cc = form["billing"]["fields"]["number"]
		form["billing"]["fields"]["number"][-4:].rjust(len(cc), "X")
		code = form["billing"]["fields"]["code"]
		form["billing"]["fields"]["code"] = "*" * len(code)

def create_transaction(amount, currency, gateway=None, data=None, reference_doc=None):
	log("Are we still using this method?\n{0}".format(get_trace()))
	transaction = frappe.get_doc({
		"doctype": "AWC Transaction",
		"status": "Initiated",
		"amount": amount,
		"currency": currency,
		"transaction_ref": "-1",
		"data": json.dumps(data or {}),
		"gateway_module": gateway or ""
	});

	if reference_doc:
		transaction.reference_doctype = reference_doc.doctype
		transaction.reference_docname = reference_doc.name

	transaction.insert(ignore_permissions=True)
	frappe.db.commit()

	return transaction

def find_transaction(refence_doc, status="Initiated"):
	log("Are we still using this method?\n{0}".format(get_trace()))
	transaction = frappe.get_doc("AWC Transaction", {"reference_doctype": ("=", reference_doc.doctype), "reference_docname": ("=", reference_doc.name), "status": status})

	return transaction

def validate_transaction_currency(currency):
	log("Are we still using this method?\n{0}".format(get_trace()))
	if currency not in ["USD"]:
		frappe.throw(
			_("Please select another payment method. '{0}' is unsupported").format(currency)
		)
