from __future__ import unicode_literals
import frappe
from awesome_cart.awc import get_template

no_sitemap = 1

def get_context(context):
    path_name = context.get("pathname", "").split('/')
    body = ""

    try:
        del context['source']
        context['awc_template'] = ''
        if path_name[0] == "awc_template":
            tpl_name = path_name[-1]
            tpl = get_template(tpl_name)
            context['awc_template'] = tpl

    except Exception as err:
        print(err)

    return context
