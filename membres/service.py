from django.db.models import Sum
from transactions.models import Benefices, Retraits, Transactions

# fonctions de rechargement de compte via l'api 
def rechargerCompteService(data):
    print("payement avec momo avec les donnees: ", data)

    return True

def investissement_actuelle(membre, devise):
    contribution = Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    retrait_investissement= Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="retrait investissement").aggregate(total=Sum('montant'))['total'] or 0
    return round(contribution - retrait_investissement)

def benefices_actuelle(membre, devise):
    benefices = float(Benefices.objects.filter(membre=membre, devise=devise, statut=True).aggregate(total=Sum('montant'))['total'] or 0)
    retrait = float(Retraits.objects.filter(membre=membre, devise=devise, statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0)
    return round(benefices - retrait)