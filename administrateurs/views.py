from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

from membres.models import Membres
from organisations.models import Organisations
from agents.models import Agents
from .models import Administrateurs, ContributionsMensuelles, CodesReference
from agents.models import Agents, NumerosAgent
from agents.forms import AgentsForm
from organisations.models import Organisations
from organisations.forms import OrganisationsForm
from transactions.models import Transactions, Prêts, TypesPrêt, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription

from .forms import AdministrateurForm
from membres.forms import MembresForm
from organisations.forms import OrganisationsForm
from transactions.forms import TransactionsForm, TypesPrêtForm, ContributionsForm, PrêtsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm
from django.utils import timezone


# Vue pour la page d'accueil des administrateurs
@login_required
def home(request):
    # Solde total de l'entreprise
    solde_total_entreprise_cdf = Transactions.objects.filter(devise="CDF").aggregate(Sum('montant'))['montant__sum'] or 0
    solde_total_entreprise_usd = Transactions.objects.filter(devise="USD").aggregate(Sum('montant'))['montant__sum'] or 0

    # Solde de toutes les dettes
    total_dettes_cdf = Prêts.objects.filter(devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_dettes_usd = Prêts.objects.filter(devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Nombre total de membres, organisations et agents
    nombre_membres = Membres.objects.count()
    nombre_organisations = Organisations.objects.count()
    nombre_agents = Agents.objects.count()


    transactions = Transactions.objects.all().order_by("-date")
    prets = Prêts.objects.filter(statut="En attente")

    transactions_inscriptions = Transactions.objects.filter(type="depot_inscription", statut="Initialisation", date_approbation=None)

    context = {
        'solde_total_entreprise_cdf': solde_total_entreprise_cdf,
        'solde_total_entreprise_usd': solde_total_entreprise_usd,
        'total_dettes_cdf': total_dettes_cdf,
        'total_dettes_usd': total_dettes_usd,
        'nombre_membres': nombre_membres,
        'nombre_organisations': nombre_organisations,
        'nombre_agents': nombre_agents,
        "transactions": transactions,
        "prets": prets,
        "inscriptions": transactions_inscriptions
    }
    return render(request, 'administrateurs/home.html', context)

# Vue pour la page de profil de l'administrateur
@login_required
def profile(request):
    administrateur = request.user.administrateurs
    if request.method == "POST":
        form = AdministrateurForm(request.POST, request.FILES, instance=administrateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour avec succès.")
            return redirect("administrateurs:profile")
    else:
        form = AdministrateurForm(instance=administrateur)
    context = {
        "form": form,
        "administrateur": administrateur,
    }
    return render(request, "administrateurs/profile.html", context)

# Vue pour la page de gestion des membres
@login_required
def membres(request):
    membres = Membres.objects.all().order_by("-date_creation")
    context = {
        "membres": membres,
    }
    return render(request, "administrateurs/membres.html", context)

# Vue pour la page de création d'un membre
@login_required
def creer_membre(request):
    if request.method == "POST":
        form = MembresForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Le membre a été créé avec succès.")
            return redirect("administrateurs:membres")
    else:
        form = MembresForm()
    return render(request, "administrateurs/creer_membre.html", {"form": form})

# Vue pour la page de voir un membre
@login_required
def voir_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)
    if request.method == "POST":
        form = MembresForm(request.POST, request.FILES, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, "Le membre a été modifié avec succès.")
            return redirect("administrateurs:membres")
    else:
        form = MembresForm(instance=membre)
        depot_form = DepotsInscriptionForm()

    context = {
        "form": form,
        "membre": membre,
        "depot_form": depot_form
    }
    return render(request, "administrateurs/voir_membre.html", context)

# Vue pour la page de modification d'un membre
@login_required
def modifier_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)
    if request.method == "POST":
        form = MembresForm(request.POST, request.FILES, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, "Le membre a été modifié avec succès.")
            return redirect("administrateurs:membres")
    else:
        form = MembresForm(instance=membre)
    context = {
        "form": form,
        "membre": membre,
    }
    return render(request, "administrateurs/modifier_membre.html", context)

# Vue pour la page de suppression d'un membre
@login_required
def supprimer_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)
    membre.delete()
    messages.success(request, "Le membre a été supprimé avec succès.")
    return redirect("administrateurs:membres")

@login_required
def accepter_membre(request, membre_id):
    membre=get_object_or_404(Membres, pk=membre_id)

    if request.method == "POST":
        form = DepotsInscriptionForm(
            request.POST,
            instance=get_object_or_404(
                DepotsInscription,
                transaction=Transactions.objects.filter(
                    membre=membre,
                    type="depot_inscription"
                ).first()
            )
        )

        if form.is_valid():
            depot = form.save(commit=False)
            depot.transaction.date_approbation = timezone.now()
            depot.statut = "En attente"
            membre = depot.transaction.membre
            membre.status = True

            membre.save()
            depot.save()
            depot.transaction.save()

            messages.success(request, "Le membre a été accepté avec succès.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
        return redirect("administrateurs:membres")

@login_required
def refuser_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)
    membre.delete()
    messages.success(request, "Le membre a été refusé avec succès.")
    return redirect("administrateurs:membres")

# Vue pour la page de gestion des organisations
@login_required
def organisations(request):
    organisations = Organisations.objects.all().order_by("-date_creation")
    context = {
        "organisations": organisations,
    }
    return render(request, "administrateurs/organisations.html", context)

# Vue pour la page de création d'une organisation
@login_required
def creer_organisation(request):
    if request.method == "POST":
        form = OrganisationsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "L'organisation a été créée avec succès.")
            return redirect("administrateurs:organisations")
    else:
        form = OrganisationsForm()
    return render(request, "administrateurs/creer_organisation.html", {"form": form})

# Vue pour la page de modification d'une organisation
@login_required
def modifier_organisation(request, organisation_id):
    organisation = get_object_or_404(Organisations, pk=organisation_id)
    if request.method == "POST":
        form = OrganisationsForm(request.POST, request.FILES, instance=organisation)
        if form.is_valid():
            form.save()
            messages.success(request, "L'organisation a été modifiée avec succès.")
            return redirect("administrateurs:organisations")
    else:
        form = OrganisationsForm(instance=organisation)
    context = {
        "form": form,
        "organisation": organisation,
    }
    return render(request, "administrateurs/modifier_organisation.html", context)

# Vue pour la page de suppression d'une organisation
@login_required
def supprimer_organisation(request, organisation_id):
    organisation = get_object_or_404(Organisations, pk=organisation_id)
    organisation.delete()
    messages.success(request, "L'organisation a été supprimée avec succès.")
    return redirect("administrateurs:organisations")

# Vue pour la page de gestion des transactions en CDF
@login_required
def transactions_cdf(request):
    transactions = Transactions.objects.filter(devise="CDF").order_by("-date")
    context = {
        "transactions": transactions,
    }
    return render(request, "administrateurs/transactions_cdf.html", context)

# Vue pour la page de gestion des transactions en USD
@login_required
def transactions_usd(request):
    transactions = Transactions.objects.filter(devise="USD").order_by("-date")
    context = {
        "transactions": transactions,
    }
    return render(request, "administrateurs/transactions_usd.html", context)

# ... (autres vues)

# Vue pour la page de gestion des types de prêt
@login_required
def types_prêt(request):
    types_prêt = TypesPrêt.objects.all()
    context = {
        "types_prêt": types_prêt,
    }
    return render(request, "administrateurs/types_prêt.html", context)

# Vue pour la page de création d'un type de prêt
@login_required
def creer_type_prêt(request):
    if request.method == "POST":
        form = TypesPrêtForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le type de prêt a été créé avec succès.")
            return redirect("administrateurs:types_prêt")  # Rediriger vers la page de gestion des types de prêt
    else:
        form = TypesPrêtForm()
    return render(request, "administrateurs/creer_type_prêt.html", {"form": form})

# Vue pour la page de modification d'un type de prêt
@login_required
def modifier_type_prêt(request, type_prêt_id):
    type_prêt = get_object_or_404(TypesPrêt, pk=type_prêt_id)
    if request.method == "POST":
        form = TypesPrêtForm(request.POST, instance=type_prêt)
        if form.is_valid():
            form.save()
            messages.success(request, "Le type de prêt a été modifié avec succès.")
            return redirect("administrateurs:types_prêt")  # Rediriger vers la page de gestion des types de prêt
    else:
        form = TypesPrêtForm(instance=type_prêt)
    context = {
        "form": form,
        "type_prêt": type_prêt,
    }
    return render(request, "administrateurs/modifier_type_prêt.html", context)

# Vue pour la page de suppression d'un type de prêt
@login_required
def supprimer_type_prêt(request, type_prêt_id):
    type_prêt = get_object_or_404(TypesPrêt, pk=type_prêt_id)
    type_prêt.delete()
    messages.success(request, "Le type de prêt a été supprimé avec succès.")
    return redirect("administrateurs:types_prêt")  # Rediriger vers la page de gestion des types de prêt

# Vue pour la page de création d'une transaction en CDF
@login_required
def creer_transaction_cdf(request):
    if request.method == "POST":
        form = TransactionsForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.devise = "CDF"  # Définir la devise à CDF
            transaction.save()
            messages.success(request, "La transaction en CDF a été créée avec succès.")
            return redirect("administrateurs:transactions_cdf")  # Rediriger vers la page des transactions en CDF
    else:
        form = TransactionsForm(initial={'devise': 'CDF'})  # Pré-remplir la devise avec CDF
    return render(request, "administrateurs/creer_transaction.html", {"form": form})

# Vue pour la page de création d'une transaction en USD
@login_required
def creer_transaction_usd(request):
    if request.method == "POST":
        form = TransactionsForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.devise = "USD"  # Définir la devise à USD
            transaction.save()
            messages.success(request, "La transaction en USD a été créée avec succès.")
            return redirect("administrateurs:transactions_usd")  # Rediriger vers la page des transactions en USD
    else:
        form = TransactionsForm(initial={'devise': 'USD'})  # Pré-remplir la devise avec USD
    return render(request, "administrateurs/creer_transaction.html", {"form": form})

# Vue pour la page de gestion des opérations (exemple)
@login_required
def opérations(request):
    # Logique pour récupérer les opérations (à adapter selon vos besoins)
    opérations = []  # Remplacez par votre logique de récupération des opérations
    context = {
        "opérations": opérations,
    }
    return render(request, "administrateurs/opérations.html", context)

# Vue pour la page de création d'une opération (exemple)
@login_required
def creer_opération(request):
    # Logique pour créer une opération (à adapter selon vos besoins)
    if request.method == "POST":
        # Logique de traitement du formulaire
        return redirect("administrateurs:opérations")  # Rediriger vers la page des opérations
    else:
        # Logique pour afficher le formulaire de création d'opération
        return render(request, "administrateurs/creer_opération.html")

# Agents Views
@login_required
def agents(request):
    agents = Agents.objects.all().order_by("-date_creation")
    context = {
        "agents": agents,
    }
    return render(request, "administrateurs/agents.html", context)


@login_required
def creer_agent(request):
    if request.method == "POST":
        form = AgentsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "L'agent a été créé avec succès.")
            return redirect("administrateurs:agents")
    else:
        form = AgentsForm()
    return render(request, "administrateurs/creer_agent.html", {"form": form})


@login_required
def voir_agent(request, agent_id):
    agent = get_object_or_404(Agents, pk=agent_id)
    if request.method == "POST":
        form = AgentsForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "L'agent a été modifié avec succès.")
            return redirect("administrateurs:agents")  # Redirect to the agent list
    else:
        form = AgentsForm(instance=agent)
    context = {
        "form": form,
        "agent": agent,
    }
    return render(request, "administrateurs/voir_agent.html", context)


@login_required
def modifier_agent(request, agent_id):
    agent = get_object_or_404(Agents, pk=agent_id)
    if request.method == "POST":
        form = AgentsForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "L'agent a été modifié avec succès.")
            return redirect("administrateurs:agents")
    else:
        form = AgentsForm(instance=agent)
    context = {
        "form": form,
        "agent": agent,
    }
    return render(request, "administrateurs/modifier_agent.html", context)


@login_required
def supprimer_agent(request, agent_id):
    agent = get_object_or_404(Agents, pk=agent_id)
    agent.delete()
    messages.success(request, "L'agent a été supprimé avec succès.")
    return redirect("administrateurs:agents")


# View for Organisations Detail
@login_required
def voir_organisation(request, organisation_id):
    organisation = get_object_or_404(Organisations, pk=organisation_id)
    context = { "organisation": organisation}
    return render(request, "administrateurs/voir_organisation.html", context)


# Administrateurs Views (Add these views)
@login_required
def administrateurs(request):
    administrateurs = Administrateurs.objects.all().order_by("-date_creation") # Make sure this query works with your model
    context = { "administrateurs": administrateurs }
    return render(request, "administrateurs/administrateurs.html", context)


@login_required
def creer_administrateur(request):
    if request.method == "POST":
        form = AdministrateurForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "L'administrateur a été créé avec succès.")
            return redirect("administrateurs:administrateurs")
    else:
        form = AdministrateurForm()
    return render(request, "administrateurs/creer_administrateur.html", {"form": form})


@login_required
def voir_administrateur(request, administrateur_id):
    administrateur = get_object_or_404(Administrateurs, pk=administrateur_id) # Correct model here
    context = {"administrateur": administrateur}
    return render(request, "administrateurs/voir_administrateur.html", context)


@login_required
def modifier_administrateur(request, administrateur_id):
    administrateur = get_object_or_404(Administrateurs, pk=administrateur_id)
    if request.method == "POST":
        form = AdministrateurForm(request.POST, request.FILES, instance=administrateur)
        if form.is_valid():
            form.save()
            messages.success(request, "L'administrateur a été modifié avec succès.")
            return redirect("administrateurs:administrateurs")
    else:
        form = AdministrateurForm(instance=administrateur)

    context = {"form": form, "administrateur": administrateur}
    return render(request, "administrateurs/modifier_administrateur.html", context)


@login_required
def supprimer_administrateur(request, administrateur_id):
    administrateur = get_object_or_404(Administrateurs, pk=administrateur_id)
    administrateur.delete()
    messages.success(request, "L'administrateur a été supprimé avec succès.")
    return redirect("administrateurs:administrateurs")

