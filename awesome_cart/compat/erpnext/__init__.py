from __future__ import unicode_literals
from awesome_cart.compat import find_compat_module

globals().update(find_compat_module('erpnext').__dict__)
