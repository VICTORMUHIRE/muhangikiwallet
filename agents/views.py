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
@verifier_agent
def home(request):
    # Récupérer les contributions et les prets de l'agent connecté
    agent = request.user.agent

    solde_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    total_prets_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="pret").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_objectif_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0
    total_retraits_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0

    transactions = Transactions.objects.filter(agent=agent).order_by("-date")
    taches = Transactions.objects.filter(agent=agent, statut="En attente").order_by("-date")
    
    context = {
        "agent": agent,
        "objectifs": objectifs,
        "total_prets_CDF": total_prets_CDF,
        "total_prets_USD": total_prets_USD,
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

                    case "pret" :
                        pret = Prêts.objects.filter(transaction=transaction).first()
                        pret.statut = "Approuvé"
                        pret.date_approbation = timezone.now()
                        pret.save()

                    case "remboursement_pret" :
                        pret = Prêts.objects.filter(transaction__membre=transaction.membre, statut="Approuvé").first()
                        pret.solde_remboursé += transaction.montant
                        
                        if pret.solde_remboursé >= pret.montant_remboursé:
                            pret.statut = pret.transaction.statut = "Remboursé"
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

@login_required
@verifier_agent
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

@login_required
@verifier_agent
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
        case "pret":
            transaction.pret.statut = "Rejeté"
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
@verifier_agent
def contributions(request):
    contributions = Contributions.objects.all().order_by("-date")
    context = {
        "contributions": contributions,
    }
    return render(request, "agents/contributions.html", context)

# Vue pour la page de gestion des prets
@login_required
@verifier_agent
def prets(request):
    prets = Prêts.objects.all().order_by("-date_demande")
    context = {
        "prets": prets,
    }
    return render(request, "agents/prets.html", context)

# Vue pour la page de gestion des types de pret
@login_required
@verifier_agent
def retraits(request):
    types_pret = TypesPrêt.objects.all()
    if request.method == "POST":
        form = TypesPrêtForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le type de pret a été ajouté avec succès.")
            return redirect("agent:types_pret")
    else:
        form = TypesPrêtForm()
    context = {
        "types_pret": types_pret,
        "form": form,
    }
    return render(request, "agents/types_pret.html", context)

# Vue pour la page de gestion des objectifs
@login_required
@verifier_agent
def objectifs(request):
    objectifs = Objectifs.objects.all().order_by("-date_debut")
    context = {
        "objectifs": objectifs,
    }
    return render(request, "agents/objectifs.html", context)

# Vue pour la page de dépôt d'objectif
@login_required
@verifier_agent
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
