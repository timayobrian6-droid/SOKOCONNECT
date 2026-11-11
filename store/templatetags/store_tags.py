from decimal import Decimal, InvalidOperation

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def ksh(value):
    """Format a number as Kenyan shillings, e.g. KSh 1,800."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    if amount == amount.to_integral():
        return f"KSh {intcomma(int(amount))}"
    return f"KSh {intcomma(f'{amount:.2f}')}"


@register.inclusion_tag("store/_stars.html")
def stars(rating):
    try:
        rating = float(rating or 0)
    except (TypeError, ValueError):
        rating = 0
    filled = int(round(rating))
    return {"states": [i < filled for i in range(5)]}


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    query = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v in (None, ""):
            query.pop(k, None)
        else:
            query[k] = v
    return query.urlencode()
