from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from membres.models import Membres
from .models import Agents
from .forms import AgentsForm
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from transactions.models import Transactions, Prets, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, RetraitsObjectif, Benefices, RemboursementsPret, AnnulationObjectif
from transactions.forms import TypesPretForm, ContributionsForm, PretsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm, TransactionsForm
from django.db.models import Sum
from django.utils import timezone
from functools import wraps


def verifier_agent(func):
    def verify(request, *args, **kwargs):
        if request.user.is_agent():
            return func(request, *args, **kwargs)
        else: return redirect("index")

    return wraps(func)(verify)

# Vue pour la page d'accueil des agents
@login_required
@verifier_agent
def home(request):
    # Récupérer les contributions et les prets de l'agent connecté
    agent = request.user.agent

    solde_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    total_prets_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut__in=["Approuvé", "Remboursé"], type="pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_USD = Transactions.objects.filter(agent=agent, devise="USD", statut__in=["Approuvé", "Remboursé"], type="pret").aggregate(total=Sum('montant'))['total'] or 0

    total_prets_rembourses_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_rembourses_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_objectif_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_retrait_objectif_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="retrait_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_retrait_objectif_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="retrait_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_annulation_objectif_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="annulation_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_annulation_objectif_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="annulation_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_inscription_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_inscription_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0
    total_retraits_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0

    transactions = Transactions.objects.filter(agent=agent).order_by("-date")
    taches = Transactions.objects.filter(agent=agent, statut="En attente").order_by("-date")
    
    context = {
        "agent": agent,
        "total_prets_CDF": float(total_prets_CDF),
        "total_prets_USD": float(total_prets_USD),
        "total_depot_objectif_CDF": float(total_depot_objectif_CDF) - float(total_retrait_objectif_CDF) - float(total_annulation_objectif_CDF),
        "total_depot_objectif_USD": float(total_depot_objectif_USD) - float(total_retrait_objectif_USD) - float(total_annulation_objectif_USD),
        "total_retraits_CDF": total_retraits_CDF,
        "total_retraits_USD": total_retraits_USD,
        "solde_CDF": float(solde_CDF) + float(total_prets_rembourses_CDF) + float(total_depot_inscription_CDF) - float(total_prets_CDF) - float(total_retraits_CDF),
        "solde_USD": float(solde_USD) + float(total_prets_rembourses_USD) + float(total_depot_inscription_USD) - float(total_prets_USD) - float(total_retraits_USD),
        "transactions": transactions,
        "taches": taches
    }

    return render(request, "agents/home.html", context)

@login_required
@verifier_agent
def depot_inscription(request):
    depots_inscriptions = DepotsInscription.objects.filter(statut="En attente").order_by("-date")
    context = {
        "depots_inscriptions": depots_inscriptions,
    }
    return render(request, "agents/depot_inscription.html", context)

@login_required
@verifier_agent
def voir_transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id, statut="En attente")

    if request.method == "POST":
        form = TransactionsForm(request.POST, request.FILES, instance=transaction)
        mot_de_passe = request.POST.get('mot_de_passe')
        
        if check_password(mot_de_passe, request.user.password):
            if form.is_valid():
                transaction = form.save(commit=False)
                transaction.date_approbation = timezone.now()
                transaction.statut = "Approuvé"

                match transaction.type:
                    case"contribution":
                        membre = transaction.membre

                        contribution = Contributions.objects.filter(transaction=transaction).first()
                        contribution.statut = "Approuvé"
                        contribution.date_approbation = timezone.now()
                        contribution.save()

                        contribution_actuelle = Contributions.objects.filter(transaction__membre=membre, mois=membre.mois_contribution, statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

                        if contribution_actuelle >= float(membre.contribution_mensuelle.montant):
                            membre.mois_contribution = membre.mois_contribution + timedelta(days=30)
                            membre.save()

                    case "pret" :
                        pret = Prets.objects.filter(transaction=transaction).first()
                        pret.statut = "Approuvé"
                        pret.date_approbation = timezone.now()
                        pret.save()

                        # Calculate benefit amount
                        montant_benefice = (float(pret.montant_remboursé) - float(pret.montant)) * 0.9 * (2800 if pret.devise == "USD" else 1)
                        devise_pret = pret.devise
                        
                        total_contributions_CDF = Transactions.objects.filter(devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
                        total_contributions_USD = Transactions.objects.filter(devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
                        
                        # Convert USD contributions to CDF for a common currency
                        total_contributions_CDF += total_contributions_USD * 2800
                        
                        membres_actifs = Membres.objects.filter(status=True)
                        
                        for membre in membres_actifs:
                            # Get member's total contributions in their respective currency
                            contributions_membre_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
                            contributions_membre_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

                            # Convert member's USD contributions to CDF
                            contributions_membre_CDF += contributions_membre_USD * 2800
                        
                            if total_contributions_CDF > 0:  # Avoid ZeroDivisionError
                                proportion = float(contributions_membre_CDF / total_contributions_CDF)
                                benefice_membre = montant_benefice * proportion
                        
                                # Determine the benefit currency based on loan currency
                                benefice_membre_usd = benefice_membre / 2800
                                Benefices.objects.create(
                                    pret=pret,
                                    membre=membre,
                                    montant=benefice_membre_usd if membre.contribution_mensuelle.devise == "USD" else benefice_membre,
                                    devise=membre.contribution_mensuelle.devise  # Use loan currency
                                )

                    case "remboursement_pret" :
                        remboursement_pret = RemboursementsPret.objects.get(transaction=transaction)
                        remboursement_pret.statut = "Approuvé"
                        remboursement_pret.save()

                        pret = remboursement_pret.pret
                        pret.solde_remboursé += transaction.montant
                        
                        if pret.solde_remboursé >= pret.montant_remboursé:
                            pret.statut = "Remboursé"
                            pret.date_remboursement = timezone.now()
                            pret.transaction.save()
                            
                        pret.save()

                    case"depot_objectif":
                        depot_objectif = DepotsObjectif.objects.filter(transaction=transaction).first()
                        objectif = depot_objectif.objectif

                        depot_objectif.statut = "Approuvé"
                        depot_objectif.date_approbation = timezone.now()
                        objectif.montant = float(objectif.montant) + float(transaction.montant)
                        
                        if objectif.montant >= objectif.montant_cible: objectif.statut = "Atteint"
                        
                        depot_objectif.objectif.save()
                        depot_objectif.save()

                    case "depot_inscription":
                        depot_inscription = DepotsInscription.objects.filter(transaction=transaction).first()
                        depot_inscription.statut = "Approuvé"
                        depot_inscription.date_approbation = timezone.now()
                        depot_inscription.save()

                    case"retrait":
                        retrait = Retraits.objects.filter(transaction=transaction).first()
                        retrait.statut = "Approuvé"
                        retrait.date_approbation = timezone.now()
                        retrait.save()

                    case "retrait_tout":
                        membre = transaction.membre

                        for pret in Prets.objects.filter(membre=membre, transaction__statut="Approuvé"):
                            pret.transaction = None
                            pret.statut = "Annulé"
                            pret.save()

                        Transactions.objects.filter(membre=membre).delete()

                        for benefice in Benefices.objects.filter(membre=membre): benefice.delete()
                        for objectif in Objectifs.objects.filter(membre=membre): objectif.delete()

                        membre.status = True
                        membre.save()

                    case "retrait_objectif":
                        retrait_objectif = RetraitsObjectif.objects.filter(transaction=transaction).first()
                        retrait_objectif.statut = "Approuvé"
                        retrait_objectif.date_approbation = timezone.now()
                        retrait_objectif.save()

                        objectif = retrait_objectif.objectif
                        objectif.statut = "Retiré"
                        objectif.save()

                    case "annulation_objectif":
                        annulation_objectif = AnnulationObjectif.objects.filter(transaction=transaction).first()
                        annulation_objectif.statut = "Approuvé"
                        annulation_objectif.date_approbation = timezone.now()
                        annulation_objectif.save()

                        objectif = annulation_objectif.objectif
                        objectif.statut = "Annulé"
                        objectif.save()

                    case _: pass

                transaction.save()
                messages.success(request, "La transaction a été approuvée avec succès")
                
                return redirect("agents:home")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")
        else:
            messages.error(request, "Mot de passe incorrect")

    else:
        form = TransactionsForm(instance=transaction)

    context = {
        "form": form,
        "transaction": transaction
    }
    return render(request, "agents/voir_transaction.html", context)

@login_required
@verifier_agent
def rejetter_transaction(request, transaction_id):
    # depot = DepotsInscription.objects.filter(transaction=get_object_or_404(Transactions, pk=transaction_id)).first()
    transaction=get_object_or_404(Transactions, pk=transaction_id)

    # depot.statut = depot.transaction.statut = "Rejeté"
    # depot.date_approbation = depot.transaction.date_approbation = timezone.now()

    transaction.statut = "Rejeté"
    transaction.date = timezone.now()

    match transaction.type:
        case "contribution":
            contribution = Contributions.objects.get(transaction=transaction)
            contribution.statut = "Rejeté"
            contribution.save()

        case "pret":
            pret = Prets.objects.get(transaction=transaction)
            pret.statut = "Rejeté"
            pret.save()

        case "remboursement_pret" :
            remboursement_pret = RemboursementsPret.objects.get(transaction=transaction)
            remboursement_pret.statut = "Rejeté"
            remboursement_pret.save()

        case "depot_objectif":
            depot_objectif = DepotsObjectif.objects.get(transaction=transaction)
            depot_objectif.statut = "Rejeté"
            depot_objectif.save()

        case "depot_inscription":
            depot_inscription = DepotsInscription.objects.get(transaction=transaction)
            depot_inscription.statut = "Rejeté"
            depot_inscription.save()

        case "retrait":
            retrait = Retraits.objects.get(transaction=transaction)
            retrait.statut = "Rejeté"
            retrait.save()

        case "retrait_objectif":
            retrait_objectif = RetraitsObjectif.objects.get(transaction=transaction)
            retrait_objectif.statut = "Rejeté"
            retrait_objectif.save()

        case "annulation_objectif":
            annulation_objectif = AnnulationObjectif.objects.get(transaction=transaction)
            annulation_objectif.statut = "Rejeté"
            annulation_objectif.save()

        case _: pass


    # depot.save()
    # depot.transaction.save()
    transaction.save()
    # messages.success(request, "Le dépôt d'inscription a été refusé avec succès")
    messages.success(request, "La transaction a été refusée avec succès")
    return redirect("agents:home")

# Vue pour la page de la liste des transactions de l'agent
@login_required
@verifier_agent
def transactions(request):
    transactions = Transactions.objects.filter(agent=request.user.agent).order_by("-date")
    context = {
        "transactions": transactions,
    }

    return render(request, "agents/transactions.html", context)

@login_required
@verifier_agent
def transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id)
    context = {
        "transaction": transaction
    }
    return render(request, "agents/transaction.html", context)

# Vue pour la page de profil de l'agent
@login_required
@verifier_agent
def profile(request):
    agent = request.user
    if request.method == "POST":
        form = AgentsForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour avec succès")
            return redirect("agent:profile")
    else:
        form = AgentsForm(instance=agent)
    context = {
        "form": form,
        "agent": agent,
    }
    return render(request, "agents/profile.html", context)

# Vue pour la page de gestion des contributions
@login_required
@verifier_agent
def contributions(request):
    contributions = Contributions.objects.all().order_by("-date")
    context = {
        "contributions": contributions,
    }
    return render(request, "agents/contributions.html", context)
