from decimal import Decimal
from celery import shared_task

from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum
from membres.service import investissement_actuelle
from transactions.models import EcheancePret, Transactions, RemboursementsPret, BalanceAdmin, Benefices, Membres

from django.db import transaction


TAUX_CHANGE = 2800
PENALITE_FIXE = 0.1  # Pénalité de 10% par défaut



def partager_benefices(pret, montant_remboursé):
    taux_interet = pret.type_pret.taux_interet / 100
    benefice = montant_remboursé * taux_interet

    # 50% pour admin
    BalanceAdmin.objects.create(
        montant=benefice / 2,
        devise=pret.devise,
        type="pret"
    )

    total_contributions = (
        (Transactions.objects.filter(devise="CDF", type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) +
        ((Transactions.objects.filter(devise="USD", type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) * TAUX_CHANGE)
    )

    if total_contributions > 0:
        membres_actifs = Membres.objects.filter(status=True)
        for membre in membres_actifs:
            contribution = (
                investissement_actuelle(membre, "CDF") +
                (investissement_actuelle(membre, "USD") * TAUX_CHANGE)
            )
            if contribution > 0:
                proportion = contribution / total_contributions
                montant_membre = (benefice / 2) * proportion
                Benefices.objects.create(
                    pret=pret,
                    membre=membre,
                    montant=montant_membre,
                    devise=pret.devise
                )

@shared_task
def remboursement_automatique_pret():
    echeances_a_traiter = EcheancePret.objects.filter(
        pret__statut="Approuvé", 
        statut__in=["en_attente", "échoué", "en_retard", "partiellement_payé"], 
        date_echeance__lte=now(), 
        montant_du__gt=Decimal('0.00') 
    ).order_by('date_echeance') 

    for echeance in echeances_a_traiter:

        with transaction.atomic(): 
            pret = echeance.pret
            membre = pret.membre
            compte = membre.compte_USD if pret.devise == "USD" else membre.compte_CDF

            montant_a_payer_pour_echeance = echeance.montant_du + echeance.penalite

            if compte.solde >= montant_a_payer_pour_echeance:

                montant_prelevé = montant_a_payer_pour_echeance

                compte.solde -= montant_prelevé
                compte.save()

                echeance.statut = "payé"
                echeance.date_paiement = now()
                echeance.penalite = Decimal('0.00')  
                echeance.grace_jusqua = None 
    
                pret.solde_remboursé += echeance.montant_du
                echeance.montant_du = Decimal('0.00') 

                echeance.save() 
                pret.save()

                Transactions.objects.create(
                    membre=membre,
                    montant=montant_prelevé, 
                    type="remboursement_pret_auto", 
                    devise=pret.devise,
                    statut="Approuvé",
                    description=f"Remboursement automatique échéance {echeance.numero} prêt {pret.pk} (incluant pénalité {echeance.penalite:.2f} {pret.devise}).",
                )

                RemboursementsPret.objects.create(
                    pret=pret,
                    montant=montant_prelevé,
                    devise=pret.devise,
                    statut="Approuvé"
                )

                partager_benefices(pret, montant_prelevé) 

                if pret.solde_remboursé >= pret.montant_payer:
                        pret.statut = "Remboursé"
                        pret.save()

            elif echeance.statut == "en_attente":
                
                echeance.statut = "échoué"
                echeance.grace_jusqua = now() + timedelta(minutes=1)
                echeance.save()
                

                print(f"Votre tentative de remboursement pour l'échéance du {echeance.date_echeance} a échoué. Veuillez recharger votre compte avant le {echeance.grace_jusqua.strftime('%d/%m/%Y %H:%M')}")

                # subject = f"Échec de remboursement de prêt N°{pret.pk} - Échéance {echeance.numero}"
                # message = f"Votre tentative de remboursement pour l'échéance du {echeance.date_echeance} a échoué. Veuillez recharger votre compte avant le {echeance.grace_jusqua.strftime('%d/%m/%Y %H:%M')}"
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [membre.email])
                # print(f"Échec de remboursement pour l'échéance {echeance.numero} du prêt {pret.pk} de {membre.nom}. Délai de grâce jusqu'au {echeance.grace_jusqua}")

            elif echeance.statut == "échoué" and now() > echeance.grace_jusqua:
                # Échec après la période de grâce, marquer en retard et appliquer la pénalité
                echeance.statut = "en_retard"
                echeance.penalite += echeance.montant * PENALITE_FIXE
                echeance.save()
                
                print(f"Votre échéance du {echeance.date_echeance} est en retard. Une pénalité de {echeance.penalite} {pret.devise} a été appliquée.")

                # Envoyer une notification de retard et de pénalité (à implémenter)
                # subject = f"Remboursement de prêt en retard N°{pret.pk} - Échéance {echeance.numero}"
                # message = f"Votre échéance du {echeance.date_echeance} est en retard. Une pénalité de {echeance.penalite} {pret.devise} a été appliquée."
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [membre.email])
                # print(f"Échéance {echeance.numero} du prêt {pret.pk} de {membre.nom} en retard. Pénalité de {echeance.penalite} appliquée.")

            elif echeance.statut == "en_retard":
                # Tenter à nouveau le paiement pour les échéances en retard (le montant_du inclut déjà la pénalité)
                pass # La tentative de paiement est gérée au début du bloc if compte.solde >= montant_du:

    print("remboursement_automatique_pret terminé.")