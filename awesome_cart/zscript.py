import frappe
import json

from frappe.utils import flt, cint

# Very simple zscript based on zbrush script language which requires no tokenization or parsing.
# Simply this is used to evaluate truthy values from nested function calls.
#
# The first value in the array is always the command, all other values are the
# arguments passed to the command.
#
# Example:
#   [ "and", true, false ]
# This will evaluate to false and is equivalent to all([true, false])
# See the COMMANDS map below
#
# Example:
#   [
#     "==",
#     [ "+", 1, 2 ],
#     [ "-", 6, 3 ]
#   ]

def get_item_stock_count(item_code):
  result = frappe.db.sql('''
    select
      sum(b.actual_qty) as qty
    from
      tabBin b, tabItem i
    where
      b.item_code = i.name
      and
      (b.projected_qty != 0 or b.reserved_qty != 0 or b.reserved_qty_for_production != 0 or b.actual_qty != 0)
      and
      b.item_code=%s
    group by
      b.actual_qty asc
  ''', [item_code], as_dict=True)

  if len(result) > 0:
    return result[0].get('qty')

  return float("inf")

COMMANDS = {
  "and": lambda *args: all(args),
  "or": lambda *args: any(args),
  "not": lambda *args: not all(args),
  "xor": lambda a, b: bool(a) ^ bool(b),
  "==": lambda a, b: a == b,
  "!=": lambda a, b: a != b,
  ">=": lambda a, b: a >= b,
  "<=": lambda a, b: a <= b,
  ">": lambda a, b: a > b,
  "<": lambda a, b: a < b,
  "+": lambda *args: reduce(lambda a, b: a + b, args),
  "-": lambda *args: reduce(lambda a, b: a - b, args),
  "*": lambda *args: reduce(lambda a, b: a * b, args),
  "/": lambda *args: reduce(lambda a, b: a / b, args),
  "true": lambda *args: True,
  "false": lambda *args: False,
  "float": flt,
  "int": cint,
  "bool": bool,
  "in": lambda needle, haystack: needle in haystack,
  "split": lambda delimiter, text: text.split(delimiter),
  "json_in": json.loads,
  "json_out": json.dumps,
  "get": lambda d, k: d.get(k),
  "ITEM_STOCK_QTY": get_item_stock_count
}

def run(script, context):
  script_obj = []
  if isinstance(script, basestring):
    script_obj = json.loads(script)

  if not isinstance(script_obj, list):
    raise Exception("ZScripts must be array of arrays")

  return execCommand(script_obj, context)

def execCommand(args, context, depth=0):
  pad = " " * depth * 2
  cmd = args[0]

  arg_values = []
  for arg in args[1:]:
    if isinstance(arg, basestring):
      arg_values += [arg.format(**context)]
    elif isinstance(arg, list) or isinstance(arg, tuple):
      arg_values += [execCommand(arg, context, depth+1)]
    else:
      arg_values += [arg]

  return COMMANDS[cmd](*arg_values)
