from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


@register.filter
def brl(value):
    """Formata número no padrão brasileiro com 2 casas decimais: 120.000,50"""
    try:
        v = Decimal(str(value))
        formatted = f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (InvalidOperation, ValueError, TypeError):
        return value


@register.filter
def brl_0(value):
    """Formata número no padrão brasileiro sem decimais: 120.000"""
    try:
        v = float(str(value))
        return f"{v:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return value
