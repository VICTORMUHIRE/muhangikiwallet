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
