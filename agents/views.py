from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Agents
from .forms import AgentsForm
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from transactions.models import Transactions, Prêts, TypesPrêt, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription
from transactions.forms import TypesPrêtForm, ContributionsForm, PrêtsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm, TransactionsForm
from django.db.models import Sum
from django.utils import timezone

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

    transactions = Transactions.objects.filter(agent=agent, statut="Approuvé").order_by("-date")
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

def voir_depot_inscription(request, transaction_id):
    form = TransactionsForm(instance=get_object_or_404(Transactions, pk=transaction_id))
    context = {
        "form": form
    }
    return render(request, "agents/voir_depot_inscription.html", context)

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
    messages.success(request, "Le dépôt d'inscription a été approuvé avec succès.")
    return redirect("agents:depot_inscription")

def rejetter_depot_inscription(request, transaction_id):
    depot = DepotsInscription.objects.filter(transaction=get_object_or_404(Transactions, pk=transaction_id)).first()
    
    depot.statut = depot.transaction.statut = "Rejeté"
    depot.date_approbation = depot.transaction.date_approbation = timezone.now()

    depot.save()
    depot.transaction.save()
    messages.success(request, "Le dépôt d'inscription a été refusé avec succès.")
    return redirect("agents:depot_inscription")

# Vue pour la page de la liste des transactions de l'agent
def transactions(request):
    transactions = Transactions.objects.filter(agent=request.user.agent).order_by("-date")
    context = {
        "transactions": transactions,
    }
    return render(request, "agents/transactions.html", context)

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
