# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
import copy
import json
import inspect

LOG_PATH = "/tmp/erpnext.log"

def log(msg):
    """Quick and dirty log method. Doesn't have size limitations as ERPNext's logs"""
    with open(LOG_PATH, 'a') as fh:
        fh.write("%s\n" % msg)
        fh.flush()

def json_default(obj):

    if isinstance(obj, datetime):
        return obj.isoformat()

    if hasattr(obj, "__dict__"):
        return str(obj) # copy.copy(obj.__dict__) #removed due to circular reference

    raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))
