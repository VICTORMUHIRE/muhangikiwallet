from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q

from membres.models import Membres
from organisations.models import Organisations
from agents.models import Agents
from .models import Administrateurs, ContributionsMensuelles, CodesReference, NumerosCompte, Users
from agents.models import Agents, NumerosAgent
from agents.forms import AgentsForm, ModifierAgentsForm
from organisations.models import Organisations
from organisations.forms import OrganisationsForm
from transactions.models import Transactions, Prêts, TypesPrêt, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices

from .forms import AdministrateurForm
from membres.forms import MembresForm, ModifierMembresForm
from organisations.forms import OrganisationsForm
from transactions.forms import TransactionsForm, TypesPrêtForm, ContributionsForm, PrêtsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm
from objectifs.models import Objectifs
from django.utils import timezone
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from random import randint
from datetime import datetime, timedelta
from django.utils import timezone
from functools import wraps

def verifier_admin(func):
    def verify(request, *args, **kwargs):
        if request.user.is_admin():
            return func(request, *args, **kwargs)
        else: return redirect("index")

    return wraps(func)(verify)

# Vue pour la page d'accueil des administrateurs
@login_required
@verifier_admin
def home(request):
    # Solde total de l'entreprise
    solde_total_entreprise_cdf = Transactions.objects.filter(devise="CDF", type="contribution").aggregate(Sum('montant'))['montant__sum'] or 0
    solde_total_entreprise_usd = Transactions.objects.filter(devise="USD", type="contribution").aggregate(Sum('montant'))['montant__sum'] or 0

    # Solde de toutes les dettes
    total_dettes_cdf = Prêts.objects.filter(devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_dettes_usd = Prêts.objects.filter(devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    total_prets_remboursees_CDF = Transactions.objects.filter(devise="CDF", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_remboursees_USD = Transactions.objects.filter(devise="USD", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0

    # Solde de toutes les dettes
    total_montant_dettes_rembouser_cdf = Prêts.objects.filter(devise="CDF", statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0
    total_montant_dettes_rembouser_usd = Prêts.objects.filter(devise="USD", statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0

    # Calcul du solde total des dépôts sur les objectifs
    total_depots_objectifs_cdf = DepotsObjectif.objects.filter(devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_depots_objectifs_usd = DepotsObjectif.objects.filter(devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Calcul du solde total des benefices
    # total_benefices_cdf = Benefices.objects.filter(devise="CDF", statut=True).aggregate(Sum('montant'))['montant__sum'] or 0
    # total_benefices_usd = Benefices.objects.filter(devise="USD", statut=True).aggregate(Sum('montant'))['montant__sum'] or 0

    # # Calcul du solde total des retraits
    total_retraits_cdf = Retraits.objects.filter(devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits_usd = Retraits.objects.filter(devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    total_benefices_cdf = float(total_montant_dettes_rembouser_cdf - total_dettes_cdf) * 0.1
    total_benefices_usd = float(total_montant_dettes_rembouser_usd - total_dettes_usd) * 0.1

    # Nombre total de membres, organisations et agents
    nombre_membres = Membres.objects.count()
    nombre_organisations = Organisations.objects.count()
    nombre_agents = Agents.objects.count()

    transactions = Transactions.objects.all().order_by("-date")
    objectifs = Objectifs.objects.filter()

    demandes_pret = Prêts.objects.filter(statut="En attente")
    demandes_inscription = DepotsInscription.objects.filter(statut="En attente")
    demandes_retrait_tout = Transactions.objects.filter(statut="En attente", type="retrait tout")
    
    context = {
        'solde_total_entreprise_cdf': float(solde_total_entreprise_cdf) + float(total_depots_objectifs_cdf) - (float(total_prets_remboursees_CDF) + float(total_retraits_cdf)),
        'solde_total_entreprise_usd': float(solde_total_entreprise_usd) + float(total_depots_objectifs_usd) - (float(total_prets_remboursees_USD) + float(total_retraits_usd)),
        'total_dettes_cdf': float(total_montant_dettes_rembouser_cdf) - float(total_prets_remboursees_CDF),
        'total_dettes_usd': float(total_montant_dettes_rembouser_usd) - float(total_prets_remboursees_USD),
        'total_depots_objectifs_cdf': total_depots_objectifs_cdf,
        'total_depots_objectifs_usd': total_depots_objectifs_usd,
        'total_benefices_cdf': total_benefices_cdf,
        'total_benefices_usd': total_benefices_usd,
        'nombre_membres': nombre_membres,
        'nombre_organisations': nombre_organisations,
        'nombre_agents': nombre_agents,
        "transactions": transactions,
        "demandes_pret": demandes_pret,
        "demandes_inscription": demandes_inscription,
        "demandes_retrait_tout": demandes_retrait_tout
    }

    return render(request, 'administrateurs/home.html', context)

# Vue pour la page de profil de l'administrateur
@login_required
@verifier_admin
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
@verifier_admin
def membres(request):
    q = request.GET.get('q', None)
    membres = Membres.objects.all().order_by('nom')  # Order by name initially

    if q:
        membres = membres.filter(
            Q(prenom__icontains=q) |
            Q(nom__icontains=q) |
            Q(postnom__icontains=q) |
            Q(numero_telephone__icontains=q)
        )

    total_contributions_CDF = Transactions.objects.filter(devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    total_contributions_USD = Transactions.objects.filter(devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
                
    # Convert USD contributions to CDF for a common currency
    total_contributions_CDF += total_contributions_USD * 2800
    
    membres_actifs = Membres.objects.filter().reverse()  # Order by id descendant

    for membre in membres:
        # Get member's total contributions in their respective currency
        membre.solde_contributions = Transactions.objects.filter(membre=membre, devise="CDF" if membre.contribution_mensuelle.devise == "CDF" else "USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
        membre.benefice_membre = Benefices.objects.filter(membre=membre).aggregate(Sum('montant'))['montant__sum'] or 0 - (Transactions.objects.filter(membre=membre, statut="Approuvé", type="retrait").aggregate(Sum('montant'))['montant__sum'] or 0)
        
        if total_contributions_CDF > 0:  # Avoid ZeroDivisionError
            membre.pourcentage = float(membre.solde_contributions * (2800 if membre.contribution_mensuelle.devise == "USD" else 1) / total_contributions_CDF) * 100

        membre.dette = Prêts.objects.filter(transaction__membre=membre, statut="Approuvé").first()
        membre.devise = "FC" if membre.contribution_mensuelle.devise == "CDF" else "$"

    paginator = Paginator(membres, 10) # Show 10 members per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'membres': page_obj,
        'page_obj': page_obj,
        'request': request
    }

    return render(request, 'administrateurs/membres.html', context)

# Vue pour la page de création d'un membre
@login_required
@verifier_admin
def creer_membre(request):
    if request.method == "POST":
        form = MembresForm(request.POST, request.FILES)
        if form.is_valid():
            membre = form.save(commit=False)

            membre.user = Users.objects.create_user(
                username=form.cleaned_data['numero_telephone'],
                # email=form.cleaned_data['email'],
                password=form.cleaned_data['mot_de_passe'],
                first_name=form.cleaned_data['nom'],
                last_name=form.cleaned_data['prenom'] or form.cleaned_data['postnom'],
                type="membre"
            )

            def generate_unique_numero():
                while True:
                    numero = f"MW-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1, 99)).ljust(2, '0')}"
                    if not NumerosCompte.objects.filter(numero=numero).exists(): break
                return numero
        
            membre.compte_CDF = NumerosCompte.objects.create(numero=generate_unique_numero(), devise="CDF")
            membre.compte_USD = NumerosCompte.objects.create(numero=generate_unique_numero(), devise="USD")
            
            membre.save()

            DepotsInscription.objects.create(membre=membre)

            messages.success(request, "Le membre a été créé avec succès.")
            return redirect("administrateurs:membres")
    else:
        form = MembresForm()
    return render(request, "administrateurs/creer_membre.html", {"form": form})

# Vue pour la page de voir un membre
@login_required
@verifier_admin
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
@verifier_admin
def modifier_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)
    if request.method == "POST":
        form = ModifierMembresForm(request.POST, request.FILES, instance=membre)
        if form.is_valid():
            form.save()
            messages.success(request, "Le membre a été modifié avec succès.")
            return redirect("administrateurs:membres")
            
    else:
        form = ModifierMembresForm(instance=membre)
    context = {
        "form": form,
        "membre": membre
    }
    return render(request, "administrateurs/modifier_membre.html", context)

# Vue pour la page de suppression d'un membre
@login_required
@verifier_admin
def supprimer_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)
    membre.delete()
    messages.success(request, "Le membre a été supprimé avec succès.")
    return redirect("administrateurs:membres")

@login_required
@verifier_admin
def accepter_membre(request, membre_id):
    membre=get_object_or_404(Membres, pk=membre_id)

    if request.method == "POST":
        form = DepotsInscriptionForm(
            request.POST,
            instance=get_object_or_404(
                DepotsInscription,
                membre=membre
            )
        )

        if form.is_valid():
            depot = form.save(commit=False)
            depot.statut = "Approuvé"
            depot.date = timezone.now()
            membre.status = True

            if "payé" in request.POST and request.POST.get("payé") == "on":
                depot.transaction = Transactions.objects.create(
                    admin=request.user.admin,
                    montant=depot.montant,
                    devise=depot.devise,
                    membre=membre,
                    statut="Approuvé",
                    type="depot_inscription"
                )

            membre.save()
            depot.save()

            messages.success(request, "Le membre a été accepté avec succès.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
        return redirect("administrateurs:membres")

@login_required
@verifier_admin
def refuser_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)

    depot=DepotsInscription.objects.get(membre=membre)
    depot.statut = "Rejeté"
    depot.save()
    membre.status = False
    membre.save()

    messages.success(request, "Le membre a été refusé avec succès.")
    return redirect("administrateurs:membres")

# Vue pour la page de gestion des organisations
@login_required
@verifier_admin
def organisations(request):
    organisations = Organisations.objects.all().order_by("-date_creation")
    context = {
        "organisations": organisations,
    }
    return render(request, "administrateurs/organisations.html", context)

# Vue pour la page de création d'une organisation
@login_required
@verifier_admin
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
@verifier_admin
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
@verifier_admin
def supprimer_organisation(request, organisation_id):
    organisation = get_object_or_404(Organisations, pk=organisation_id)
    organisation.delete()
    messages.success(request, "L'organisation a été supprimée avec succès.")
    return redirect("administrateurs:organisations")

# Vue pour la page de gestion des transactions en CDF
@login_required
@verifier_admin
def transactions(request):
    transactions = Transactions.objects.filter().order_by("-date")
    context = {
        "transactions": transactions,
    }
    return render(request, "administrateurs/transactions.html", context)

@login_required
@verifier_admin
def transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id)
    context = {
        "transaction": transaction
    }
    return render(request, "administrateurs/transaction.html", context)

# Vue pour la page de gestion des types de pret
@login_required
@verifier_admin
def types_pret(request):
    types_pret = TypesPrêt.objects.all()
    context = {
        "types_pret": types_pret,
    }
    return render(request, "administrateurs/types_pret.html", context)

# Vue pour la page de création d'un type de pret
@login_required
@verifier_admin
def creer_type_pret(request):
    if request.method == "POST":
        form = TypesPrêtForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le type de pret a été créé avec succès.")
            return redirect("administrateurs:types_pret")  # Rediriger vers la page de gestion des types de pret
    else:
        form = TypesPrêtForm()
    return render(request, "administrateurs/creer_type_pret.html", {"form": form})

# Vue pour la page de modification d'un type de pret
@login_required
@verifier_admin
def modifier_type_pret(request, type_pret_id):
    type_pret = get_object_or_404(TypesPrêt, pk=type_pret_id)
    if request.method == "POST":
        form = TypesPrêtForm(request.POST, instance=type_pret)
        if form.is_valid():
            form.save()
            messages.success(request, "Le type de pret a été modifié avec succès.")
            return redirect("administrateurs:types_pret")  # Rediriger vers la page de gestion des types de pret
    else:
        form = TypesPrêtForm(instance=type_pret)
    context = {
        "form": form,
        "type_pret": type_pret,
    }
    return render(request, "administrateurs/modifier_type_pret.html", context)

# Vue pour la page de suppression d'un type de pret
@login_required
@verifier_admin
def supprimer_type_pret(request, type_pret_id):
    type_pret = get_object_or_404(TypesPrêt, pk=type_pret_id)
    type_pret.delete()
    messages.success(request, "Le type de pret a été supprimé avec succès.")
    return redirect("administrateurs:types_pret")  # Rediriger vers la page de gestion des types de pret

# Vue pour la page de création d'une transaction en CDF
@login_required
@verifier_admin
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
@verifier_admin
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

@login_required
@verifier_admin
def agents(request):
    agents = Agents.objects.all().order_by('nom')
    q = request.GET.get('q', None)

    if q:
        agents = agents.filter(
            Q(prenom__icontains=q) |
            Q(nom__icontains=q) |
            Q(postnom__icontains=q) |
            Q(numero_telephone__icontains=q)
        )

    for agent in agents:
        agent.total_depot_inscription_usd = 0
        agent.total_contributions_usd = 0
        agent.total_prets_usd = 0
        agent.total_remboursements_prets_usd = 0
        agent.total_retraits_usd = 0
        agent.total_objectifs_usd = 0

        for devise, rate in {"CDF": 2800, "USD": 1}.items():  # Replace with your dynamic rate fetching
            agent.total_depot_inscription_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="depot_inscription", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_contributions_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_prets_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="pret", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_remboursements_prets_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="remboursement_pret", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_retraits_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="retrait", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_objectifs_usd += float(Transactions.objects.filter(agent=agent, devise=devise, statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate # Correct this line

        agent.total_transactions_usd = (
            agent.total_contributions_usd -
            agent.total_prets_usd +
            agent.total_remboursements_prets_usd -
            agent.total_retraits_usd +
            agent.total_depot_inscription_usd
        )


    paginator = Paginator(agents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {
        'agents': page_obj,
        'page_obj': page_obj,
        "request": request,

    }
    return render(request, "administrateurs/agents.html", context)

@login_required
@verifier_admin
def creer_agent(request):
    if request.method == "POST":
        form = AgentsForm(request.POST, request.FILES)
        if form.is_valid():
            agent = form.save(commit=False)

            agent.user = Users.objects.create_user(
                username=form.cleaned_data['numero_telephone'],
                # email=form.cleaned_data['email'],
                password=form.cleaned_data['mot_de_passe'],
                first_name=form.cleaned_data['nom'],
                last_name=form.cleaned_data['prenom'] or form.cleaned_data['postnom'],
                type="agent"
            )

            agent.save()

            messages.success(request, "L'agent a été créé avec succès.")
            return redirect("administrateurs:agents")
    else:
        form = AgentsForm()
    return render(request, "administrateurs/creer_agent.html", {"form": form})

@login_required
@verifier_admin
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
@verifier_admin
def modifier_agent(request, agent_id):
    agent = get_object_or_404(Agents, pk=agent_id)
    if request.method == "POST":
        form = ModifierAgentsForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "L'agent a été modifié avec succès.")
            return redirect("administrateurs:agents")
    else:
        form = ModifierAgentsForm(instance=agent)
    context = {
        "form": form,
        "agent": agent,
    }
    return render(request, "administrateurs/modifier_agent.html", context)

@login_required
@verifier_admin
def supprimer_agent(request, agent_id):
    agent = get_object_or_404(Agents, pk=agent_id)
    agent.delete()
    messages.success(request, "L'agent a été supprimé avec succès.")
    return redirect("administrateurs:agents")

# View for Organisations Detail
@login_required
@verifier_admin
def voir_organisation(request, organisation_id):
    organisation = get_object_or_404(Organisations, pk=organisation_id)
    context = { "organisation": organisation}
    return render(request, "administrateurs/voir_organisation.html", context)

# Administrateurs Views (Add these views)
@login_required
@verifier_admin
def administrateurs(request):
    administrateurs = Administrateurs.objects.all().order_by("-date_creation") # Make sure this query works with your model
    context = { "administrateurs": administrateurs }
    return render(request, "administrateurs/administrateurs.html", context)

@login_required
@verifier_admin
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
@verifier_admin
def voir_administrateur(request, administrateur_id):
    administrateur = get_object_or_404(Administrateurs, pk=administrateur_id) # Correct model here
    context = {"administrateur": administrateur}
    return render(request, "administrateurs/voir_administrateur.html", context)

@login_required
@verifier_admin
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
@verifier_admin
def supprimer_administrateur(request, administrateur_id):
    administrateur = get_object_or_404(Administrateurs, pk=administrateur_id)
    administrateur.delete()
    messages.success(request, "L'administrateur a été supprimé avec succès.")
    return redirect("administrateurs:administrateurs")

@login_required
@verifier_admin
def prets(request):
    prets = Prêts.objects.all().order_by("-date")
    context = {"prets": prets}
    return render(request, "administrateurs/prets.html", context)

@login_required
@verifier_admin
def voir_pret(request, pret_id):
    pret = get_object_or_404(Prêts, pk=pret_id)

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))
    
    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                pret.date_approbation = timezone.now()
                pret.administrateur = request.user.admin

                transaction = transaction_form.save(commit=False)

                transaction.membre = pret.membre
                transaction.agent = transaction.numero_agent.agent
                transaction.type = "pret"
                transaction.statut = "En attente"
                pret.statut = "Approuvé"
                
                pret.transaction = transaction

                pret.transaction.save()
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
                        
                        print(f"{total_contributions_USD = } {total_contributions_CDF = } {contributions_membre_CDF = } {contributions_membre_USD = } {contributions_membre_CDF = } {montant_benefice = } {proportion =  } {benefice_membre = }")
                
                messages.success(request, "Le pret a été approuvé et les bénéfices distribués avec succès.")
                return redirect("administrateurs:voir_pret", pret_id=pret.pk)
            
        else:
            messages.error(request, "Mot de passe incorrect")
    
    context = {
        "form": PrêtsForm(instance=pret),
        "transaction_form": TransactionsForm(),
        "numeros_categories": numeros_categories,
        "pret": pret
    }
    
    return render(request, "administrateurs/voir_pret.html", context)

@login_required
@verifier_admin
def rejeter_pret(request, pret_id):
    pret = get_object_or_404(Prêts, pk=pret_id)

    pret.statut = "Rejeté"
    pret.date = timezone.now()
    pret.save()
    messages.success(request, "Le pret a été rejeté avec succès.")
    return redirect("administrateurs:voir_pret", pret_id=pret.pk)

@login_required
@verifier_admin
def demande_retrait_tout(request, retrait_id):
    retrait = get_object_or_404(Transactions, pk=retrait_id, type="retrait tout")
    membre = retrait.membre

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST, instance=retrait)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid() or True:

                retrait.date_approbation = timezone.now()
                retrait.administrateur = request.user.admin

                depot_inscription = DepotsInscription.objects.get(transaction__membre=membre)
                # depot_inscription.statut = "En attente"
                depot_inscription.transaction = None
                depot_inscription.save()

                for pret in Prêts.objects.filter(transaction__membre=membre, statut__in=["Approuvé", "Remboursé"]):
                    pret.transaction = None
                    pret.save()

                Transactions.objects.filter(membre=membre).delete()

                for benefice in Benefices.objects.filter(membre=membre): benefice.delete()
                for objectif in Objectifs.objects.filter(membre=membre): objectif.delete()

                retrait.statut = "Approuvé"
                retrait.save()

                membre.status = True
                membre.save()

                messages.success(request, "Le retrait a été approuvé avec succès.")
                return redirect("administrateurs:home")

            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")
        else:
            messages.error(request, "Mot de passe incorrect")
    
    montant_contributions = Transactions.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    objectifs = Objectifs.objects.filter(membre=membre)
    montant_objectifs = ((DepotsObjectif.objects.filter(transaction__membre=membre, devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) + (DepotsObjectif.objects.filter(transaction__membre=membre, devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) * 2800) * (1/2800 if membre.contribution_mensuelle.devise == "USD" else 1)
    montant_benefices = Benefices.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, statut=True).aggregate(Sum('montant'))['montant__sum'] or 0

    context = {
        "form": TransactionsForm(instance=retrait),
        "numeros_categories": numeros_categories,
        "retrait": retrait,
        "membre": membre,
        "montant_contributions": montant_contributions,
        "objectifs": objectifs,
        "montant_objectifs": montant_objectifs,
        "montant_benefices": montant_benefices,
        "montant_total": float(montant_contributions) + montant_objectifs + float(montant_benefices)
}

    return render(request, "administrateurs/voir_retrait_tout.html", context)

@login_required
@verifier_admin
def refuser_retrait_tout(request, retrait_id):
    retrait = get_object_or_404(Transactions, pk=retrait_id, type="retrait tout")
    retrait.statut = "Rejeté"
    retrait.date = timezone.now()
    retrait.save()
    messages.success(request, "Le retrait a été rejeté avec succès.")
    return redirect("administrateurs:home")
