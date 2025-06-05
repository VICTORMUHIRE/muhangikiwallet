from celery import shared_task
import time

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from django.db.models import Sum
from membres.service import investissement_actuelle
from transactions.models import EcheancePret, Prets, Transactions, RemboursementsPret, BalanceAdmin, Benefices, Membres


@shared_task
def hello_world_task():
    print("Hello World!")
    time.sleep(2)

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

# tache de remboursement automatique
@shared_task
def remboursement_automatique_pret():
    echeances = EcheancePret.objects.filter(
        pret__statut="Approuvé",
        statut__in=["en_attente", "échoué", "en_retard"],
        date_echeance__lte=now()
    ).order_by('date_echeance')

    for echeance in echeances:
        pret = echeance.pret
        membre = pret.membre
        compte = membre.compte_USD if pret.devise == "USD" else membre.compte_CDF
        montant_du = echeance.montant + echeance.penalite

        if compte.solde >= montant_du:
            # Paiement réussi
            compte.solde -= montant_du
            compte.save()

            echeance.statut = "payé"
            echeance.date_paiement = now()
            echeance.penalite = 0  # Réinitialiser la pénalité après paiement
            echeance.grace_jusqua = None # Réinitialiser la date de grâce
            echeance.save()

            pret.solde_remboursé += echeance.montant
            pret.save()

            Transactions.objects.create(
                membre=membre,
                montant=echeance.montant,
                type="remboursement_pret",
                devise=pret.devise,
                statut="Approuvé",
                description=f"Remboursement automatique échéance {echeance.numero} prêt {pret.pk}",
            )

            RemboursementsPret.objects.create(
                pret=pret,
                montant=echeance.montant,
                devise=pret.devise,
                statut="Approuvé"
            )

            partager_benefices(pret, echeance.montant)

            if pret.solde_remboursé >= pret.montant_payer:
                pret.statut = "Remboursé"
                pret.save()

        elif echeance.statut == "en_attente":
            # Premier échec de paiement
            echeance.statut = "échoué"
            echeance.grace_jusqua = now() + timedelta(minutes=1)
            echeance.save()
            # Envoyer une notification à l'utilisateur (à implémenter)

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

    print("remboursement_automatique_pret terminé")