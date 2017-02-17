from __future__ import unicode_literals
import os
import importlib

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
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), module))
    module_version = importlib.import_module(module).__version__
    module_versions_avail = avail_versions(module_path)
    match = match_version(module_version, module_versions_avail)

    if match is None:
        raise Exception("Unsupported %s version v%s. Lowest supported version is %s" % (module, module_version, "v%s.%s.%s" % module_versions_avail[0]))

    module_import_name = "v%s_%s_%s" % match
    print("[AWC] Importing Compatibility Module: %s %s" % (module, "v%s.%s.%s" % match))
    return importlib.import_module('.%s.%s' % (module, module_import_name), 'awesome_cart.compat')
