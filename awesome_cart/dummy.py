# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe

def get_shipping_rates(items, address):
	# the account(char of accounts) which this charge is recorded
	account = "Freight and Forwarding Charges - A"
	return [
		{ "label": "Dummy NextDay", "fee": 5.0, "id": "Dummy Next Day", "carrier": "Dummy", "account": account },
		{ "label": "Dummy NextHour", "fee": 50.0, "id": "Dummy Next Hour", "carrier": "Dummy", "account": account },
		{ "label": "Dummy NextMinute", "fee": 500.0, "id": "Dummy Next Minute", "carrier": "Dummy", "account": account },
		{ "label": "Dummy NextSecond", "fee": 5000.0, "id": "Dummy Next Second", "carrier": "Dummy", "account": account }
	]
