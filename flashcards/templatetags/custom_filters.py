from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import escape
import re

register = template.Library()

@register.filter
def truncate(h, amount):
  if len(h) > amount:
    return h[0:amount-3]+"..."
  return h

@register.filter
def index(h, i):
  return h[i]