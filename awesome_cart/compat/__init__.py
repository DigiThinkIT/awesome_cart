from __future__ import unicode_literals
import os
import importlib

def version_distance(a, b):
    """Calculates +/- distance between two tuples, one element at a time"""
    for i in range(0, len(a)):
        r = a[i] - b[i]
        if r != 0:
            return r
    return 0

def avail_versions(current_path=None):
    """Scans directory for version modules and returns a list of versions"""
    if current_path is None:
        current_path = os.path.abspath(os.path.dirname(__file__))
    print(current_path)
    versions = [tuple(int(y) for y in x[1:].split('_')) for x in next(os.walk(current_path))[1] if x[0] == 'v']
    versions.sort()
    return versions

def match_version(version, versions):
    """Finds the closest module version matching the running version"""
    v = tuple(int(y) for y in version.split('.'))
    closest = min(versions, key=lambda x: version_distance(x, v))
    return closest

def find_compat_module(module):
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "_%s" % module))
    module_version = importlib.import_module(module).__version__
    module_versions_avail = avail_versions(module_path)
    match = match_version(module_version, module_versions_avail)
    module_import_name = "v%s_%s_%s" % match
    print module_import_name
    return importlib.import_module('._%s.%s' % (module, module_import_name), 'awesome_cart.compat')

erpnext = find_compat_module('erpnext')
frappe = find_compat_module('frappe')
