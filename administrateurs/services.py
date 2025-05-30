from datetime import timedelta
from transactions.models import EcheancePret

def generer_echeances(pret):
    date_debut = pret.date_approbation.date()
    delais = pret.type_pret.delai_remboursement  
    semaines_par_mois = 4

    if pret.mode_payement == "mensuel":
        nb_echeances = delais
        interval = timedelta(days=30)
    elif pret.mode_payement == "hebdomadaire":
        nb_echeances = delais * semaines_par_mois  
        interval = timedelta(weeks=1)
    else:
        raise ValueError("Mode de paiement non pris en charge.")

    montant_par_echeance = pret.montant_payer / nb_echeances

    for i in range(nb_echeances):
        date_echeance = date_debut + interval * (i + 1)

        EcheancePret.objects.create(
            pret=pret,
            numero=i + 1,
            date_echeance=date_echeance,
            montant=montant_par_echeance
        )

    # Fixer la date de remboursement à la date de la dernière échéance
    pret.date_remboursement = date_debut + interval * nb_echeances
    pret.save()

def generer_echeances_test_minutes(pret, nombre_echeances=10, intervalle_minutes=4):

    date_debut = pret.date_approbation

    date_courante = date_debut  # Initialiser date_courante à la date de début
    numero = 1

    if nombre_echeances <= 0 or pret.montant_payer <= 0:
        return  # Éviter les erreurs si le nombre d'échéances ou le montant est invalide

    montant_par_echeance = pret.montant_payer / nombre_echeances

    for i in range(nombre_echeances):
        date_courante += timedelta(minutes=intervalle_minutes) # Incrémenter AVANT de créer l'échéance
        EcheancePret.objects.create(
            pret=pret,
            numero=numero,
            date_echeance=date_courante,
            montant=montant_par_echeance
        )
        numero += 1

        print(f"({numero}, {date_courante.strftime('%d/%m/%Y %H:%M:%S')}) \n")