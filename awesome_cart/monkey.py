from __future__ import unicode_literals
import types
from .dbug import log, deprecated

deprecated("""This Module is deprecated from an earlier version of the cart.
			  It is safe to remove once all other references are gone""")

def patch_method(obj, method, override):
    """Monkey Patch helper. Will override an object's method with a custome one"""
    log("patch_method(%s, %s, %s)" % (str(obj), method, override.__name__))
    orig = getattr(obj, method)
    if hasattr(orig, "monkeypatched") and orig.monkeypatched == override:
        return

    override.patched_method = orig

    def __fn(*args, **kwargs):
        return override(*args, **kwargs)
    __fn.monkeypatched = override

    setattr(obj, method, __fn)
