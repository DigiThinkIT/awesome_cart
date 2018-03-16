"""
# Integrating Credit Gateway

### 1. Validate Currency Support

Example:

	from frappe.integration_broker.doctype.integration_service.integration_service import get_integration_controller

	controller = get_integration_controller("Credit Gateway")
	controller().validate_transaction_currency(currency)

### 2. Redirect for payment

Example:

	payment_details = {
		"amount": 600,
		"title": "Payment for bill : 111",
		"description": "payment via cart",
		"reference_doctype": "Payment Request",
		"reference_docname": "PR0001",
		"payer_email": "NuranVerkleij@example.com",
		"payer_name": "Nuran Verkleij",
		"order_id": "111",
		"currency": "USD"
	}

	# redirect the user to this url
	url = controller().get_payment_url(**payment_details)


### 3. On Completion of Payment

Write a method for `on_payment_authorized` in the reference doctype

Example:

	def on_payment_authorized(payment_status):
		# your code to handle callback

##### Note:

payment_status - payment gateway will put payment status on callback.
For authorize.net status parameter is one from: [Completed, Failed]


More Details:

"""

from __future__ import unicode_literals
import frappe
import json
import urllib
from frappe import _, _dict
from frappe.model.document import Document
from frappe.utils import get_url, call_hook_method
from frappe.integrations.utils import create_request_log, create_payment_gateway
from awesome_cart import awc
from awesome_cart.compat.customer import get_current_customer
from dti_devtools.debug import log

class CreditGatewaySettings(Document):
	service_name = "Credit Gateway"
	supported_currencies = ["USD"]
	is_embedable = True

	def validate(self):
		create_payment_gateway("Credit Gateway")
		call_hook_method("payment_gateway_enabled", gateway=self.service_name)

	def on_update(self):
		pass

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_("Please select another payment method. {0} does not support transactions in currency \"{1}\"").format(self.service_name, currency))

	def get_payment_url(self, **kwargs):
		url = "./integrations/credit_gateway/{0},{1}"
		return get_url(url.format(kwargs["reference_doctype"], kwargs["reference_docname"]))

	def is_available(self, context={}, is_backend=0):

		# never available to backend
		if is_backend:
			return False

		customer = get_current_customer()

		if customer:
			# disabled until Eric figures out if JHA wants to check against credit
			#return context["total_credit"] > 0
			self.get_embed_context(context)

			# test for either allow_billme_later or can_billme_later role

			return customer.get("allow_billme_later", False) or "Bill Me Later User" in frappe.get_roles()

		return False

	def get_embed_context(self, context):
		awc_session = awc.get_awc_session()
		reference_doc = {}

		if context.get("reference_doctype") and context.get("reference_docname"):
			reference_doc = frappe.get_doc(context.get("reference_doctype"), context.get("reference_docname"))

		# gets current cart quotation with customer selection modifications applied
		quotation = awc._get_cart_quotation(awc_session) or {}

		# lets figure out which customer is placing an order
		customer_source_list = [
			context.get("customer_name"),			# implicit customer
			reference_doc.get("customer"),			# customer link field
			reference_doc.get("customer_name"),		# alternative customer link field
			awc_session.get("selected_customer"),	# awc cart customer selection
			quotation.get("customer")				# at worst case get current cart quotation
		]

		# get first valid customer name
		customer_name = next((name for name in customer_source_list if name is not None), None)

		# if we have a customer, lets extract dashboard info
		if customer_name:
			customer = frappe.get_doc("Customer", customer_name)
			customer.load_dashboard_info()
			info = customer.get("__onload", {}).get("dashboard_info")

			if info:
				context["currency"] = info["currency"]
				context["total_unpaid"] = info["total_unpaid"] or 0
				context["total_credit"] = customer.credit_limit or 0

	def get_embed_form(self, context={}):

		context.update({
			"source": "templates/includes/integrations/credit_gateway/embed.html"
		})
		context = _dict(context)

		self.get_embed_context(context)

		return {
			"form": frappe.render_template(context.source, context),
			"context": context,
			"style_url": "/assets/css/credit_gateway_embed.css",
			"script_url": "/assets/js/credit_gateway_embed.js"
		}

	def create_request(self, data):
		# simulates a transaction by just submitting a quotation
		# if there is enough credit available there should be no issues

		self.process_data = frappe._dict(data)

		self.billing_info = self.process_data.get("billing_info")
		self.shipping_info = self.process_data.get("shipping_info")

		redirect_url = ""
		redirect_to = data.get("notes", {}).get("redirect_to") or None
		redirect_message = data.get("notes", {}).get("redirect_message") or None
		status = "Completed"

		if not self.process_data.get("unittest"):
			self.integration_request = create_request_log(self.process_data, "Host", self.service_name)
			self.integration_request.status = status
			self.integration_request.save()

		custom_redirect_to = None
		try:
			if not self.process_data.get("unittest"):
				ref_doc = frappe.get_doc(
					self.process_data.reference_doctype,
					self.process_data.reference_docname)

				ref_doc.flags["skip_payment_request"] = 1

				custom_redirect_to = ref_doc.run_method("on_payment_authorized", status)
		except Exception as ex:
			log(frappe.get_traceback())
			raise ex

		if custom_redirect_to:
			redirect_to = custom_redirect_to

		redirect_url = "/integrations/credit_success"
		redirect_message = "Continue Shopping"
		success = True

		params = []
		if redirect_to:
			params.append(urllib.urlencode({"redirect_to": redirect_to}))
		if redirect_message:
			params.append(urllib.urlencode({"redirect_message": redirect_message}))

		if len(params) > 0:
			redirect_url += "?" + "&".join(params)

		self.process_data = {}
		self.billing_info = {}
		self.shipping_info = {}

		return {
			"redirect_to": redirect_url,
			"error": redirect_message if status == "Failed" else None,
			"status": status
		}

@frappe.whitelist()
def get_service_details():
	return """
		<div>
			<p> This is a simple gateway to enable Customers with credit above all unpaid totals + the current order
		</div>
	"""

@frappe.whitelist(allow_guest=True)
def process(options):
	data = {}

	# handles string json as well as dict argument
	if isinstance(options, basestring):
		options = json.loads(options)

	data.update(options)

	data = frappe.get_doc("Credit Gateway Settings").create_request(data)

	frappe.db.commit()
	return data
