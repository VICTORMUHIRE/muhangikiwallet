from celery import shared_task
import time

from datetime import timedelta
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



@shared_task
def remboursement_automatique_pret():
    print("Début de la tâche de remboursement automatique de prêt.")

    # Inclure le nouveau statut 'partiellement_payé' dans le filtre
    # Et assurez-vous de filtrer sur 'montant_du' > 0 car les échéances payées auront montant_du = 0
    echeances_a_traiter = EcheancePret.objects.filter(
        pret__statut="Approuvé", # Seuls les prêts approuvés sont traités
        statut__in=["en_attente", "échoué", "en_retard", "partiellement_payé"], # Inclure le nouveau statut
        date_echeance__lte=now(), # Échéances dont la date est passée
        montant_du__gt=Decimal('0.00') # Seules les échéances ayant un solde dû
    ).order_by('date_echeance') # Traiter les plus anciennes d'abord

    print(f"Nombre d'échéances à traiter: {echeances_a_traiter.count()}")

    for echeance in echeances_a_traiter:
        try:
            with transaction.atomic(): # Assure l'atomicité pour chaque échéance
                pret = echeance.pret
                membre = pret.membre
                compte = membre.compte_USD if pret.devise == "USD" else membre.compte_CDF

                # Montant exact à payer pour cette échéance (solde dû + pénalité)
                montant_a_payer_pour_echeance = echeance.montant_du + echeance.penalite
                
                print(f"Traitement échéance {echeance.numero} (Prêt {pret.pk}) - Statut: {echeance.statut}, Montant dû: {echeance.montant_du:.2f}, Pénalité: {echeance.penalite:.2f}, Total à payer: {montant_a_payer_pour_echeance:.2f}")
                print(f"Solde du compte de {membre.user.username}: {compte.solde:.2f} {compte.devise}")

                if compte.solde >= montant_a_payer_pour_echeance:
                    # --- Paiement complet de l'échéance (incluant pénalité) ---
                    montant_prelevé = montant_a_payer_pour_echeance

                    compte.solde -= montant_prelevé
                    compte.save()

                    echeance.statut = "payé"
                    echeance.date_paiement = now()
                    echeance.penalite = Decimal('0.00')  # Réinitialiser la pénalité
                    echeance.grace_jusqua = None # Réinitialiser la date de grâce
                    echeance.montant_du = Decimal('0.00') # L'échéance est entièrement payée
                    echeance.save()

                    # pret.solde_remboursé doit être incrémenté du MONTANT ORIGINAL DE L'ÉCHÉANCE (capital + intérêt)
                    # car `montant_payer` du prêt est la somme des `echeance.montant` originaux.
                    # Si echeance.montant_du a été réduit par avance, c'est `echeance.montant - echeance.montant_du_initial` qui a été payé.
                    # Pour être précis, il faut toujours incrémenter `pret.solde_remboursé` du montant d'intérêt+capital *réellement* payé.
                    # Comme `montant_du` est le reste à payer, si on le met à 0, le montant principal de l'échéance a été couvert.
                    # Donc on peut ajouter l'original `echeance.montant` à `pret.solde_remboursé` si l'échéance est désormais 'payé'.
                    
                    # Correction: Pret.solde_remboursé doit être la somme des montants capital+interet payés pour les échéances.
                    # Lorsque echeance.montant_du devient 0, cela signifie que echeance.montant (original) est couvert.
                    pret.solde_remboursé += echeance.montant # Ajoute le montant original de l'échéance (capital+intérêt)
                    pret.nombre_echeances_payees += 1 # Incrémente le nombre d'échéances payées
                    pret.save()

                    Transactions.objects.create(
                        membre=membre,
                        montant=montant_prelevé, # La transaction inclut la pénalité si payée
                        type="remboursement_pret_auto", # Type spécifique pour auto-remboursement
                        devise=pret.devise,
                        statut="Approuvé",
                        description=f"Remboursement automatique échéance {echeance.numero} prêt {pret.pk} (incluant pénalité {echeance.penalite:.2f} {pret.devise}).",
                    )

                    RemboursementsPret.objects.create(
                        pret=pret,
                        montant=montant_prelevé, # Le montant remboursé inclut la pénalité
                        devise=pret.devise,
                        statut="Approuvé",
                        echeance=echeance, # Lier au modèle d'échéance si votre RemboursementsPret le permet
                        # Note: Si RemboursementsPret est censé suivre uniquement les montants du prêt
                        # sans pénalité, ajustez ici. Pour cet exemple, il inclut la pénalité.
                    )

                    # Partager les bénéfices sur le montant d'intérêt de l'échéance originale.
                    # La fonction `partager_benefices` s'attend au montant qui contribue au bénéfice.
                    # Ici, c'est le montant original de l'échéance, sans la pénalité.
                    partager_benefices(pret, echeance.montant) # `echeance.montant` est le montant original (capital+intérêt)

                    print(f"Échéance {echeance.numero} du prêt {pret.pk} entièrement payée automatiquement.")

                elif compte.solde > Decimal('0.00') and compte.solde < montant_a_payer_pour_echeance:
                    # --- Paiement partiel de l'échéance (incluant pénalité) ---
                    montant_paye_par_auto = compte.solde # Prélever tout ce qui est disponible sur le compte
                    
                    # Déduire de la pénalité en premier, puis du montant_du
                    if echeance.penalite > Decimal('0.00'):
                        if montant_paye_par_auto >= echeance.penalite:
                            montant_restant_apres_penalite = montant_paye_par_auto - echeance.penalite
                            echeance.penalite = Decimal('0.00') # Pénalité entièrement couverte
                            montant_paye_sur_du = montant_restant_apres_penalite
                        else:
                            echeance.penalite -= montant_paye_par_auto # Pénalité partiellement couverte
                            montant_paye_sur_du = Decimal('0.00')
                    else:
                        montant_paye_sur_du = montant_paye_par_auto

                    echeance.montant_du -= montant_paye_sur_du # Diminuer le solde dû de l'échéance
                    echeance.statut = "partiellement_payé" # Mettre à jour le statut
                    echeance.save()

                    compte.solde -= montant_paye_par_auto # Le solde du compte devient zéro
                    compte.save()

                    # pret.solde_remboursé doit être incrémenté de la partie capital+intérêt payée.
                    # C'est `montant_paye_sur_du`.
                    pret.solde_remboursé += montant_paye_sur_du
                    pret.save()

                    Transactions.objects.create(
                        membre=membre,
                        montant=montant_paye_par_auto, # La transaction enregistre le montant total prélevé
                        type="remboursement_pret_auto_partiel", # Type spécifique pour auto-remboursement partiel
                        devise=pret.devise,
                        statut="Approuvé",
                        description=f"Remboursement automatique partiel échéance {echeance.numero} prêt {pret.pk}. Restant dû: {echeance.montant_du:.2f} {pret.devise}.",
                    )

                    RemboursementsPret.objects.create(
                        pret=pret,
                        montant=montant_paye_par_auto, # Le montant remboursé inclut la partie de pénalité couverte
                        devise=pret.devise,
                        statut="Approuvé",
                        echeance=echeance,
                    )

                    # Partage des bénéfices sur la portion d'intérêt/capital payée (montant_paye_sur_du)
                    partager_benefices(pret, montant_paye_sur_du)

                    print(f"Échéance {echeance.numero} du prêt {pret.pk} partiellement payée automatiquement. Montant restant dû: {echeance.montant_du:.2f} {pret.devise}")

                else:
                    # --- Solde insuffisant pour le paiement ---
                    print(f"Solde insuffisant pour l'échéance {echeance.numero} du prêt {pret.pk}. Solde: {compte.solde:.2f} {compte.devise}, Nécessaire: {montant_a_payer_pour_echeance:.2f} {pret.devise}.")

                    # Logique existante pour les statuts "échoué" et "en_retard"
                    if echeance.statut == "en_attente":
                        echeance.statut = "échoué"
                        # Vérifiez que timedelta est bien `minutes` ou ce qui convient pour vos tests
                        echeance.grace_jusqua = now() + timedelta(minutes=1)
                        echeance.save()
                        print(f"Échéance {echeance.numero} du prêt {pret.pk} a échoué. Délai de grâce jusqu'au {echeance.grace_jusqua.strftime('%d/%m/%Y %H:%M')}")

                    elif echeance.statut == "échoué" and now() > echeance.grace_jusqua:
                        echeance.statut = "en_retard"
                        # Appliquer la pénalité si elle n'a pas déjà été appliquée pour cet état
                        if echeance.penalite == Decimal('0.00'): # Appliquer la pénalité une seule fois quand elle passe en retard
                            echeance.penalite += echeance.montant_du * PENALITE_FIXE # Pénalité sur le montant dû restant
                            print(f"Pénalité de {echeance.penalite:.2f} {pret.devise} appliquée pour l'échéance {echeance.numero} du prêt {pret.pk}.")
                        echeance.save()
                        print(f"Échéance {echeance.numero} du prêt {pret.pk} en retard. Pénalité ajoutée.")

                    # Si statut est déjà "en_retard", rien de plus à faire ici pour le moment.
                    # La tentative de paiement échouera simplement si le solde reste insuffisant.

            # Après chaque traitement d'échéance (qu'elle soit payée, partiellement payée ou échouée)
            # Vérifier si le prêt est entièrement remboursé.
            if pret.solde_remboursé >= pret.montant_payer and pret.statut != "Remboursé":
                # Vérifier également s'il ne reste plus d'échéances en attente/en retard/partiellement payées
                # car `solde_remboursé` peut être >= `montant_payer` mais il reste des pénalités dues.
                # Ou si toutes les échéances ont leur `montant_du` à 0.
                if not pret.echeances.filter(montant_du__gt=Decimal('0.00')).exists():
                    pret.statut = "Remboursé"
                    pret.date_remboursement = now()
                    pret.save()
                    print(f"Prêt {pret.pk} de {membre.user.username} entièrement remboursé !")
                else:
                    print(f"Prêt {pret.pk} a un solde remboursé suffisant mais des échéances avec solde dû existent toujours.")


        except Exception as e:
            # Enregistrer l'erreur pour cette échéance mais permettre à la tâche de continuer
            print(f"Erreur lors du traitement de l'échéance {echeance.numero} du prêt {echeance.pret.pk}: {e}")
            import traceback
            traceback.print_exc()
            # Optionnel: marquer l'échéance ou le prêt comme ayant une erreur pour une révision manuelle

    print("remboursement_automatique_pret terminé.")