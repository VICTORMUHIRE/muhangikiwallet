from django import template
from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def pourcentage(montant, montant_cible):
    try:
        montant = float(montant)
        montant_cible = float(montant_cible)
        return (montant / montant_cible) * 100 if montant_cible > 0 else 0
    except (TypeError, ValueError, ZeroDivisionError):
        return 0

@register.filter
def objectif_statut_count(objectifs, statut):
    return sum(1 for objectif in objectifs if objectif.statut == statut)

@register.filter
def prets_statut_count(prets, statut):
    return sum(1 for pret in prets if pret.statut == statut)

@register.filter(name='pourcentage_inverse')
def pourcentage_inverse(value, total):
    try:
        value = float(value)
        total = float(total)
        if total == 0:
            return "0.00"
        pourcentage = (value / total) * 100
        pourcentage_inverse_val = 100 - pourcentage
        return f"{pourcentage_inverse_val:.2f}"
    except (ValueError, TypeError):
        return "0.00"


@register.filter(name='dict_item')
def dict_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def subtract_days(date, days):
    if isinstance(date, (int, float)):
        date = datetime.date.fromtimestamp(date)
    if hasattr(date, 'day'):
        try:
            return date - timedelta(days=int(days))
        except ValueError:
            return date
    return ''