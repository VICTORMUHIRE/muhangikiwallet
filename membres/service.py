from django.db.models import Sum
from transactions.models import Transactions

# fonctions de rechargement de compte via l'api 
def rechargerCompteService(data):
    print("payement avec momo avec les donnees: ", data)

    return True

def investissement_actuelle(membre, devise):
    contribution = Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    retrait_investissement= Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="retrait investissement").aggregate(total=Sum('montant'))['total'] or 0
    return round(contribution - retrait_investissement)