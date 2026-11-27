from django import template

register = template.Library()


# muestra el número con puntos de miles: 2500000 -> 2.500.000
@register.filter
def puntos(valor):
    return '{:,}'.format(valor).replace(',', '.')
