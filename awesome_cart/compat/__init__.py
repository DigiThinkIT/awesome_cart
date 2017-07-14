from __future__ import unicode_literals
import os

def avail_versions(current_path=None):
	"""Scans directory for version modules and returns a list of versions"""
	if current_path is None:
		current_path = os.path.abspath(os.path.dirname(__file__))
	versions = [tuple(int(y) for y in x[1:].split('_')) for x in next(os.walk(current_path))[1] if x[0] == 'v']
	versions.sort()
	return versions

def match_version(version, versions):
	"""Finds the closest module version matching the running version"""
	v = tuple(int(y) for y in version.split('.'))
	ret_version = None
	for ver in versions:
		if ver <= v and ver > ret_version:
			ret_version = ver

	return ret_version

def find_compat_module(module):
	import importlib
	cur_frappe = importlib.import_module("frappe")

	# allows explicit compat version overrides
	compat_version_overrides = cur_frappe.local.conf.get("awc_compat", {})
	version_overwritten = 0

	module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), module))
	module_version = importlib.import_module(module).__version__

	module_version_actual = module_version
	if compat_version_overrides.get(module):
		version_overwritten = 1
		module_version = compat_version_overrides[module]
		print("[AWC] Module Version Override: %s %s => %s" % (module, module_version_actual, module_version))

	module_versions_avail = avail_versions(module_path)
	match = match_version(module_version, module_versions_avail)

	if match is None:
		raise Exception("Unsupported %s version v%s. Lowest supported version is %s" % (module, module_version, "v%s.%s.%s" % module_versions_avail[0]))

	module_import_name = "v%s_%s_%s" % match
	print("[AWC] Importing Compatibility Module: %s %s" % (module, "v%s.%s.%s" % match))
	return importlib.import_module('.%s.%s' % (module, module_import_name), 'awesome_cart.compat')

class CompatException(Exception):
	def __init__(self, *args, **kwargs):
		super(CompatException, self).__init__(*args, **kwargs)

	def toResult(result):
		result["success"] = False
		result["msg"] = str(self)

class ArgumentMissingError(CompatException):
	def __init__(self, argument):
		super(ArgumentMissing, self).__init__("Argument Missing: {}".format(argument))
