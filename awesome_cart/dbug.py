# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import copy
import json
import inspect

import frappe

from datetime import datetime
from os.path import splitext, basename
from frappe.model.base_document import BaseDocument

LOG_PATH = "/tmp/erpnext.log"

def method_proxy(*fn_list):
	"""Helper to proxy multiple methods calls with identicall arguments.
	Returns a proxy function which returns the last method's return value.

	Ex:
		output_fn = proxy_fn(print, frappe.logger().debug)
		output_fn("Hello World!")
	"""

	def proxy_fn(*args, **kwargs):
		result = None
		for fn in fn_list:
			result = fn(*args, **kwargs)

		return result;

	return proxy_fn

_log = method_proxy(print, frappe.logger().debug)

def log(*args, **kwargs):
	fmt=kwargs.get("fmt", "-- [{function_name}:{line_number}] at {filename}")
	line_fmt=kwargs.get("line_fmt", "   {0}")
	trace=kwargs.get("trace", False)

	(frame, filename, line_number,
	 function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]

	if len(args) > 1:
		msg = str(args[0]).format(*args[1:])
	else:
		msg = str(args[0])

	output = []
	output.append(fmt.format(
		filename=filename,
		line_number=line_number,
		function_name=function_name,
		line=lines[0].strip(),
		index=index
	))
	output += [line_fmt.format(line) for line in iter(msg.splitlines()) ]
	if trace:
		output.append(get_trace(skip=1))

	_log("\n".join(output))

def get_trace(fmt="File \"{filename}\", line {line_number}, in {function_name}\n  {line}", skip=0):
	output = []
	stack = inspect.getouterframes(inspect.currentframe())[1+skip:]
	for (frame, filename, line_number, function_name, lines, index) in reversed(stack):
		output.append(fmt.format(
			filename=filename,
			line_number=line_number,
			function_name=function_name,
			line=lines[0].strip(),
			index=index
		))

	return "\n".join(output)


def deprecated(message, help=None, line_message="Deprecated", warning="Warning", trace=True, output_fn=_log):
	"""This is a utility function used to warn of deprected calls."""

	(frame, filename, line_number,
	 function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[2]

	output = []
	output.append(" ---- Deprecation {0}!".format(warning))
	output.append("")
	output += [ "      {0}".format(line.strip()) for line in iter(message.strip().splitlines()) ]
	output.append("")
	output.append("   -- File    : {0}".format(filename))
	output.append("   -- Line    : {0}".format(line_number))
	if function_name == "<module>":
		output.append("   -- Module  : {0}".format(inspect.getmoduleinfo(filename)))
	else:
		output.append("   -- Function: {0}".format(function_name))
	output.append("")

	for line in lines:
		output.append("                {0}".format(line.strip()))

	output.append("                {0}\__ {1}".format(" " * index, line_message))

	if help:
		output.append("")
		output += [ "      {0}".format(line.strip()) for line in iter(help.strip().splitlines()) ]

	if trace:
		output.append("")
		output.append(get_trace(skip=1))

	output.append("")

	output_fn("\n".join(output))

def json_default(obj):
	"""A helper function used as an argument to json.dumps which prettifies json output
	ex:
		json.dumps(<some object>, default=json_default)

	"""

	if isinstance(obj, datetime):
		return obj.isoformat()

	if hasattr(obj, "as_dict"):
		return obj.as_dict()

	if hasattr(obj, "__dict__"):
		return str(obj) # copy.copy(obj.__dict__) #removed due to circular reference

	try:
		return str(obj)
	except Exception as ex:
		print(ex)
		raise TypeError("Unserializable object {0} of type {1}".format(obj, type(obj)))

def pretty_json(obj):
	"""Utility function to output prettified json data"""
	return json.dumps(obj, indent=4, default=json_default)
