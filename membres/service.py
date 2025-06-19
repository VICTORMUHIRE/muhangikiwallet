from django.db.models import Sum
from transactions.models import AnnulationObjectif, Benefices, DepotsObjectif, Retraits, RetraitsObjectif, Transactions


def investissement_actuelle(membre, devise):
    contribution = Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    retrait_investissement= Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="retrait_investissement").aggregate(total=Sum('montant'))['total'] or 0
    return contribution - retrait_investissement

def benefices_actuelle(membre, devise):
    benefices = Benefices.objects.filter(membre=membre, devise=devise).aggregate(total=Sum('montant'))['total'] or 0
    retrait = Retraits.objects.filter(membre=membre,transaction__type = "retrait_benefice" , devise=devise ).aggregate(total=Sum('montant'))['total'] or 0
    return benefices - retrait

def objectifs_actuelle(membre, devise):
    depot = DepotsObjectif.objects.filter(membre=membre, devise=devise).aggregate(total=Sum('montant'))['total'] or 0
    retrait = RetraitsObjectif.objects.filter(membre=membre, devise=devise).aggregate(total=Sum('montant'))['total'] or 0
    annulation = AnnulationObjectif.objects.filter(membre=membre, devise=devise).aggregate(total=Sum('montant'))['total'] or 0
    return depot - retrait -  annulation

