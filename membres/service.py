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

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone

def generer_statut_echeances(pret):
    """
    Génère une liste de statuts d'échéances pour un prêt donné.

    Args:
        pret: L'instance du modèle Prets.

    Returns:
        Une liste de dictionnaires, où chaque dictionnaire représente une échéance
        avec sa date de fin et son statut ('Payé', 'Non payé', 'En attente', 'Dépassé').
    """
    echeances = []
    if pret.statut == 'Approuvé' and pret.date_approbation and pret.date_remboursement:
        date_debut = pret.date_approbation.date()
        date_fin = pret.date_remboursement.date()
        montant_a_payer = pret.montant_payer
        mode_payement = pret.mode_payement
        montant_remboursé = pret.solde_remboursé
        date_aujourdhui = timezone.now().date()

        if mode_payement == 'hebdomadaire':
            delta = date_fin - date_debut
            total_semaines = delta.days // 7 if delta.days >= 0 else 0
            if total_semaines > 0:
                montant_par_echeance = montant_a_payer / total_semaines
                for i in range(total_semaines):
                    date_echeance = date_debut + timedelta(weeks=i + 1)
                    statut_paiement = "Non payé"

                    # Logique de vérification du statut (à affiner avec votre modèle de paiement)
                    if montant_remboursé >= montant_par_echeance * (i + 1):
                        statut_paiement = "Payé"
                    elif date_echeance < date_aujourdhui:
                        statut_paiement = "Dépassé"
                    else:
                        statut_paiement = "En attente"

                    echeances.append({
                        'numero': i + 1,
                        'date_fin': date_echeance,
                        'montant_attendu': montant_par_echeance,
                        'statut': statut_paiement,
                    })
        elif mode_payement == 'mensuel':
            # Calculer le nombre total de mois
            rel_delta = relativedelta(date_fin, date_debut)
            total_mois = rel_delta.months + rel_delta.years * 12
            if total_mois > 0:
                montant_par_echeance = montant_a_payer / total_mois
                for i in range(total_mois):
                    # Ajouter 1 mois à la date de début pour chaque échéance
                    date_echeance = date_debut + relativedelta(months=i + 1)
                    statut_paiement = "Non payé"

                    # Logique de vérification du statut (à affiner avec votre modèle de paiement)
                    if montant_remboursé >= montant_par_echeance * (i + 1):
                        statut_paiement = "Payé"
                    elif date_echeance < date_aujourdhui:
                        statut_paiement = "Dépassé"
                    else:
                        statut_paiement = "En attente"

                    echeances.append({
                        'numero': i + 1,
                        'date_fin': date_echeance,
                        'montant_attendu': montant_par_echeance,
                        'statut': statut_paiement,
                    })
        # Ajouter d'autres logiques pour d'autres modes de paiement si nécessaire

    return echeances