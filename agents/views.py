from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Agents
from .forms import AgentsForm
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from transactions.models import Transactions, Prêts, TypesPrêt, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription
from transactions.forms import TypesPrêtForm, ContributionsForm, PrêtsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm, TransactionsForm
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
def home(request):
    # Récupérer les contributions et les prêts de l'agent connecté
    agent = request.user.agent

    solde_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    total_prêts_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="prêt").aggregate(total=Sum('montant'))['total'] or 0
    total_prêts_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="prêt").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_objectif_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0
    total_retraits_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0

    transactions = Transactions.objects.filter(agent=agent).order_by("-date")
    taches = Transactions.objects.filter(agent=agent, statut="En attente").order_by("-date")
    
    context = {
        "agent": agent,
        "objectifs": objectifs,
        "total_prêts_CDF": total_prêts_CDF,
        "total_prêts_USD": total_prêts_USD,
        "total_depot_objectif_CDF": total_depot_objectif_CDF,
        "total_depot_objectif_USD": total_depot_objectif_USD,
        "total_retraits_CDF": total_retraits_CDF,
        "total_retraits_USD": total_retraits_USD,
        "solde_CDF": solde_CDF,
        "solde_USD": solde_USD,
        "transactions": transactions,
        "taches": taches
    }
    return render(request, "agents/home.html", context)

def depot_inscription(request):
    depots_inscriptions = DepotsInscription.objects.filter(statut="En attente").order_by("-date")
    context = {
        "depots_inscriptions": depots_inscriptions,
    }
    return render(request, "agents/depot_inscription.html", context)

def voir_transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id)

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

                    case "prêt" :
                        prêt = Prêts.objects.filter(transaction=transaction).first()
                        prêt.statut = "Approuvé"
                        prêt.date_approbation = timezone.now()
                        prêt.save()

                    case "remboursement_prêt" :
                        prêt = Prêts.objects.filter(transaction__membre=transaction.membre, statut="Approuvé").first()
                        prêt.solde_remboursé += transaction.montant
                        
                        if prêt.solde_remboursé >= prêt.montant_remboursé:
                            prêt.statut = prêt.transaction.statut = "Remboursé"
                            prêt.date_remboursement = timezone.now()
                            prêt.transaction.save()
                            
                        prêt.save()

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
        "form": form
    }
    return render(request, "agents/voir_transaction.html", context)

def approuver_depot_inscription(request, transaction_id):
    # depot = DepotsInscription.objects.filter(transaction=get_object_or_404(Transactions, pk=transaction_id)).first()
    transaction=get_object_or_404(Transactions, pk=transaction_id)
    
    # depot.statut = depot.transaction.statut = "Approuvé"
    # depot.date_approbation = depot.transaction.date_approbation = timezone.now()

    transaction.statut = "Approuvé"
    transaction.date_approbation = timezone.now()

    # depot.save()
    # depot.transaction.save()
    transaction.save()
    # messages.success(request, "Le dépôt d'inscription a été approuvé avec succès")
    messages.success(request, "La transaction a été approuvée avec succès")
    return redirect("agents:home")

def rejetter_depot_inscription(request, transaction_id):
    # depot = DepotsInscription.objects.filter(transaction=get_object_or_404(Transactions, pk=transaction_id)).first()
    transaction=get_object_or_404(Transactions, pk=transaction_id)

    # depot.statut = depot.transaction.statut = "Rejeté"
    # depot.date_approbation = depot.transaction.date_approbation = timezone.now()

    transaction.statut = "Rejeté"
    transaction.date = timezone.now()

    match transaction.type:
        case "contribution":
            transaction.contribution.statut = "Rejeté"
        case "prêt":
            transaction.prêt.statut = "Rejeté"
        case "depot_objectif":
            transaction.depot_objectif.statut = "Rejeté"
        case "depot_inscription":
            transaction.depot_inscription.statut = "Rejeté"
        case "retrait":
            transaction.retrait.statut = "Rejeté"
        case _:
            pass


    # depot.save()
    # depot.transaction.save()
    transaction.save()
    # messages.success(request, "Le dépôt d'inscription a été refusé avec succès")
    messages.success(request, "La transaction a été refusée avec succès")
    return redirect("agents:home")

# Vue pour la page de la liste des transactions de l'agent
def transactions(request):
    transactions = Transactions.objects.filter(agent=request.user.agent).order_by("-date")
    context = {
        "transactions": transactions,
    }
    return render(request, "agents/transactions.html", context)

@login_required
def transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id)
    context = {
        "transaction": transaction
    }
    return render(request, "agents/transaction.html", context)

# Vue pour la page de profil de l'agent
@login_required
def profile(request):
    agent = request.user
    if request.method == "POST":
        form = AgentsForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour avec succès.")
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
def contributions(request):
    contributions = Contributions.objects.all().order_by("-date")
    context = {
        "contributions": contributions,
    }
    return render(request, "agents/contributions.html", context)

# Vue pour la page de gestion des prêts
@login_required
def prêts(request):
    prêts = Prêts.objects.all().order_by("-date_demande")
    context = {
        "prêts": prêts,
    }
    return render(request, "agents/prêts.html", context)

# Vue pour la page de gestion des types de prêt
@login_required
def retraits(request):
    types_prêt = TypesPrêt.objects.all()
    if request.method == "POST":
        form = TypesPrêtForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le type de prêt a été ajouté avec succès.")
            return redirect("agent:types_prêt")
    else:
        form = TypesPrêtForm()
    context = {
        "types_prêt": types_prêt,
        "form": form,
    }
    return render(request, "agents/types_prêt.html", context)

# Vue pour la page de gestion des objectifs
@login_required
def objectifs(request):
    objectifs = Objectifs.objects.all().order_by("-date_debut")
    context = {
        "objectifs": objectifs,
    }
    return render(request, "agents/objectifs.html", context)

# Vue pour la page de dépôt d'objectif
@login_required
def parametres(request, objectif_id):
    objectif = get_object_or_404(Objectifs, pk=objectif_id)
    if request.method == "POST":
        montant = float(request.POST["montant"])
        if montant > 0:
            objectif.montant += montant
            objectif.save()
            messages.success(request, f"Vous avez déposé {montant} CDF sur l'objectif {objectif.name}.")
            return redirect("agent:objectifs")
        else:
            messages.error(request, "Veuillez entrer un montant valide.")
    return render(request, "agents/depot_objectif.html", {"objectif": objectif})
