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


# tache de remboursement automatique


@shared_task

def remboursement_automatique_pret():

    prets = Prets.objects.filter(statut="Approuvé")


    for pret in prets:

        # if pret.mode_payement == "hebdomadaire":

        #     periode = timedelta(weeks=1)

        # elif pret.mode_payement == "mensuel":

        #     periode = timedelta(days=30)

        # else:

        #     continue



        # Simulation : réduction des délais pour tester rapidement

        if pret.mode_payement == "hebdomadaire":

            periode = timedelta(minutes=2)  # simulation au lieu de weeks=1

        elif pret.mode_payement == "mensuel":

            periode = timedelta(minutes=4)  # simulation au lieu de days=30

        else:

            continue  # Sauter les cas non définis


        # Dernière date de remboursement ou approbation du prêt

        derniere_remboursement = RemboursementsPret.objects.filter(pret=pret, statut="Approuvé").order_by('-date').first()

        date_reference = derniere_remboursement.date if derniere_remboursement else pret.date_approbation

        if not date_reference:

            continue


        # Vérifier si le délai est écoulé

        if now() >= date_reference + periode and pret.solde_remboursé < pret.montant_payer:

            montant_par_periode = pret.montant_remboursé

            membre = pret.membre

            compte = membre.compte_USD if pret.devise == "USD" else membre.compte_CDF


            if compte.solde >= montant_par_periode:

                # Débiter le compte

                compte.solde -= montant_par_periode

                


                # Enregistrer le remboursement

                pret.solde_remboursé += montant_par_periode

                


                # Créer et enregistrer la transaction liee au remboursement

                Transactions.objects.create(

                    membre = pret.membre,

                    montant = montant_par_periode,

                    type = "remboursement_pret",

                    statut = "Approuvé",

                    description = f"Remboursement automatique du prêt N°{pret.pk}",

                )


                RemboursementsPret.objects.create(

                    pret=pret,

                    montant=montant_par_periode,

                    devise=pret.devise,

                    statut="Approuvé"

                )


                #Calcul du bénéfice

                taux_interet = pret.type_pret.taux_interet / 100

                benefice = montant_par_periode * taux_interet


                #50% pour admin

                BalanceAdmin.objects.create(

                    montant=benefice / 2,

                    devise=pret.devise,

                    type="pret"

                )


                #50% pour membres contributeurs

                total_contributions = (

                    (Transactions.objects.filter(devise="CDF", type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) +

                    ((Transactions.objects.filter(devise="USD", type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) * TAUX_CHANGE)

                )


                if total_contributions > 0:

                    membres_actifs = Membres.objects.filter(status=True)

                    for membre in membres_actifs:

                        contribution_membre = (investissement_actuelle(membre, "CDF") + (investissement_actuelle(membre, "USD")*TAUX_CHANGE))

                        if contribution_membre > 0:

                            proportion = contribution_membre / total_contributions

                            montant_membre = (benefice / 2) * proportion


                            Benefices.objects.create(

                                pret=pret,

                                membre=membre,

                                montant=montant_membre,

                                devise=pret.devise

                            )


                #enregistrement des modifications

                pret.save()

                compte.save()


                #Prêt totalement remboursé

                if pret.solde_remboursé >= pret.montant_payer:

                    pret.statut = "Remboursé"

                    pret.save()


            else:

                # Solde insuffisant

                RemboursementsPret.objects.create(

                    pret=pret,

                    montant=montant_par_periode,

                    devise=pret.devise,

                    statut="Échoué"

                )

                print(f"REMBOURSEMENT ÉCHOUÉ : membre {membre.nom} n'a pas assez de solde pour payer {montant_par_periode} {pret.devise}")


    print("remboursement_automatique_pret effectue")