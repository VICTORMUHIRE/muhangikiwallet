from django import template

register = template.Library()

@register.filter
def pourcentage(montant, montant_cible):
    try:
        montant = float(montant)
        montant_cible = float(montant_cible)
        return (montant / montant_cible) * 100 if montant_cible > 0 else 0
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
