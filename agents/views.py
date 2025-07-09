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
from transactions.models import Transactions, Prets, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, RetraitsObjectif, Benefices, RemboursementsPret, AnnulationObjectif, BalanceAdmin, RetraitsAdmin
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

    total_prets_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut__in=["Approuvé", "Remboursé", "Depassé"], type="pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_USD = Transactions.objects.filter(agent=agent, devise="USD", statut__in=["Approuvé", "Remboursé", "Depassé"], type="pret").aggregate(total=Sum('montant'))['total'] or 0

    total_prets_rembourses_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_rembourses_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_objectif_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_retrait_objectif_CDF = RetraitsObjectif.objects.filter(transaction__agent=agent, devise="CDF", transaction__statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0
    total_retrait_objectif_USD = RetraitsObjectif.objects.filter(transaction__agent=agent, devise="USD", transaction__statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    total_annulation_objectif_CDF = AnnulationObjectif.objects.filter(transaction__agent=agent, devise="CDF", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0
    total_annulation_objectif_USD = AnnulationObjectif.objects.filter(transaction__agent=agent, devise="USD", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_inscription_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_inscription_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_CDF = Transactions.objects.filter(agent=agent, devise="CDF", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0
    total_retraits_USD = Transactions.objects.filter(agent=agent, devise="USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_admin_CDF = Transactions.objects.filter(agent=agent, devise="CDF", type="retrait_admin", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits_admin_USD = Transactions.objects.filter(agent=agent, devise="USD", type="retrait_admin", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    
    total_retraits_tout_CDF = Transactions.objects.filter(agent=agent, devise="CDF", type="retrait_tout", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits_tout_USD = Transactions.objects.filter(agent=agent, devise="USD", type="retrait_tout", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

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
        "solde_CDF": float(solde_CDF) + float(total_prets_rembourses_CDF) + float(total_depot_inscription_CDF) + float(total_annulation_objectif_CDF)/10 - float(total_prets_CDF) - float(total_retraits_CDF) - float(total_retraits_tout_CDF) - float(total_retraits_admin_CDF),
        "solde_USD": float(solde_USD) + float(total_prets_rembourses_USD) + float(total_depot_inscription_USD) + float(total_annulation_objectif_USD)/10 - float(total_prets_USD) - float(total_retraits_USD) - float(total_retraits_tout_USD) - float(total_retraits_admin_USD),
        "transactions": transactions,
        "taches": taches
    }

    return render(request, "agents/home.html", context)

@login_required
@verifier_agent
def prets(request):
    prets = Prets.objects.filter(transaction__agent=request.user.agent, statut__in=["Approuvé", "Depassé"]).order_by("-date_remboursement")

    for pret in prets:
        if pret.statut == "Approuvé" and timezone.now() > pret.date_remboursement:
            pret.montant_remboursé += 5 * (2800 if pret.devise == "CDF" else 1)
            pret.statut = "Depassé"
            pret.save()
            
    context = {"prets": prets}
    return render(request, "agents/prets.html", context)


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
                   
                    case "depot_inscription":
                        depot_inscription = DepotsInscription.objects.filter(transaction=transaction).first()
                        depot_inscription.statut = "Approuvé"
                        depot_inscription.date_approbation = timezone.now()
                        depot_inscription.save()

                        BalanceAdmin.objects.create(
                            montant=transaction.montant,
                            devise=transaction.devise,
                            type="depot_inscription"
                        )

                    case "retrait":
                        retrait = Retraits.objects.filter(transaction=transaction).first()
                        retrait.statut = "Approuvé"
                        retrait.date_approbation = timezone.now()
                        retrait.save()

                        BalanceAdmin.objects.create(
                            montant=float(transaction.montant) * retrait.frais,
                            devise=transaction.devise,
                            type="retrait"
                        )

                    case "retrait_admin":
                        retrait_admin = RetraitsAdmin.objects.filter(transaction=transaction).first()
                        retrait_admin.statut = "Approuvé"
                        retrait_admin.date_approbation = timezone.now()
                        retrait_admin.save()

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
    transaction = get_object_or_404(Transactions, pk=transaction_id)

    transaction.statut = "Rejeté"
    transaction.date = timezone.now()

    match transaction.type:
        case "pret":
            pret = Prets.objects.get(transaction=transaction)
            pret.statut = "Rejeté"
            pret.save()

        case "depot_inscription":
            depot_inscription = DepotsInscription.objects.get(transaction=transaction)
            depot_inscription.statut = "Rejeté"
            depot_inscription.save()

        case "retrait":
            retrait = Retraits.objects.get(transaction=transaction)
            retrait.statut = "Rejeté"
            retrait.save()

        case "retrait_admin":
            retrait_admin = RetraitsAdmin.objects.get(transaction=transaction)
            retrait_admin.statut = "Rejeté"
            retrait_admin.save()



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
