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
def home(request):
    # Solde total de l'entreprise
    solde_total_entreprise_cdf = Transactions.objects.filter(devise="CDF", type="contribution").aggregate(Sum('montant'))['montant__sum'] or 0
    solde_total_entreprise_usd = Transactions.objects.filter(devise="USD", type="contribution").aggregate(Sum('montant'))['montant__sum'] or 0

    # Solde de toutes les dettes
    total_dettes_cdf = Prêts.objects.filter(devise="CDF", statut__in=["Approuvé", "Remboursé"]).aggregate(Sum('montant'))['montant__sum'] or 0
    total_dettes_usd = Prêts.objects.filter(devise="USD", statut__in=["Approuvé", "Remboursé"]).aggregate(Sum('montant'))['montant__sum'] or 0

    # Solde de toutes les dettes
    total_montant_dettes_rembouser_cdf = Prêts.objects.filter(devise="CDF", statut__in=["Approuvé", "Remboursé"]).aggregate(Sum('montant_remboursé'))['montant_remboursé__sum'] or 0
    total_montant_dettes_rembouser_usd = Prêts.objects.filter(devise="USD", statut__in=["Approuvé", "Remboursé"]).aggregate(Sum('montant_remboursé'))['montant_remboursé__sum'] or 0

    # Calcul du solde total des dépôts sur les objectifs
    total_depots_objectifs_cdf = DepotsObjectif.objects.filter(devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_depots_objectifs_usd = DepotsObjectif.objects.filter(devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Calcul du solde total des benefices
    # total_benefices_cdf = Benefices.objects.filter(devise="CDF", statut=True).aggregate(Sum('montant'))['montant__sum'] or 0
    # total_benefices_usd = Benefices.objects.filter(devise="USD", statut=True).aggregate(Sum('montant'))['montant__sum'] or 0

    # # Calcul du solde total des retraits
    # total_retraits_cdf = Retraits.objects.filter(devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    # total_retraits_usd = Retraits.objects.filter(devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    total_benefices_cdf = float(total_montant_dettes_rembouser_cdf - total_dettes_cdf) * 0.1
    total_benefices_usd = float(total_montant_dettes_rembouser_usd - total_dettes_usd) * 0.1

    # Nombre total de membres, organisations et agents
    nombre_membres = Membres.objects.count()
    nombre_organisations = Organisations.objects.count()
    nombre_agents = Agents.objects.count()

    transactions = Transactions.objects.all().order_by("-date")
    objectifs = Objectifs.objects.filter()

    demandes_prêt = Prêts.objects.filter(statut="En attente"),
    demandes_inscription = DepotsInscription.objects.filter(statut="En attente")
    
    context = {
        'solde_total_entreprise_cdf': solde_total_entreprise_cdf,
        'solde_total_entreprise_usd': solde_total_entreprise_usd,
        'total_dettes_cdf': total_montant_dettes_rembouser_cdf,
        'total_dettes_usd': total_montant_dettes_rembouser_usd,
        'total_depots_objectifs_cdf': total_depots_objectifs_cdf,
        'total_depots_objectifs_usd': total_depots_objectifs_usd,
        'total_benefices_cdf': total_benefices_cdf,
        'total_benefices_usd': total_benefices_usd,
        'nombre_membres': nombre_membres,
        'nombre_organisations': nombre_organisations,
        'nombre_agents': nombre_agents,
        "transactions": transactions,
        "demandes_prêt": demandes_prêt,
        "demandes_inscription": demandes_inscription,
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
            
    membres_actifs = Membres.objects.filter(status=True)

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
                membre=membre
            )
        )

        if form.is_valid():
            depot = form.save(commit=False)
            depot.statut = "Approuvé"
            depot.date = timezone.now()
            membre.status = True

            membre.save()
            depot.save()

            messages.success(request, "Le membre a été accepté avec succès.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
        return redirect("administrateurs:membres")

@login_required
def refuser_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)

    transaction=Transactions.objects.get(membre=membre, type="depot_inscription")
    transaction.statut = "Rejeté"
    transaction.date = transaction.depot_inscription.date = timezone.now()
    transaction.save()
    membre.status = False
    membre.save()

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
def transactions(request):
    transactions = Transactions.objects.filter().order_by("-date")
    context = {
        "transactions": transactions,
    }
    return render(request, "administrateurs/transactions.html", context)

@login_required
def transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id)
    context = {
        "transaction": transaction
    }
    return render(request, "administrateurs/transaction.html", context)

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

@login_required
def prêts(request):
    prêts = Prêts.objects.all().order_by("-date")
    context = {"prêts": prêts}
    return render(request, "administrateurs/prêts.html", context)

@login_required
def voir_prêt(request, prêt_id):
    prêt = get_object_or_404(Prêts, pk=prêt_id)

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
                prêt.date_approbation = timezone.now()
                prêt.administrateur = request.user.admin

                transaction = transaction_form.save(commit=False)

                transaction.membre = prêt.membre
                transaction.agent = transaction.numero_agent.agent
                transaction.type = "prêt"
                transaction.statut = "En attente"
                prêt.statut = "Approuvé"
                
                prêt.transaction = transaction

                prêt.transaction.save()
                prêt.save()
            
                # Calculate benefit amount
                montant_benefice = (float(prêt.montant_remboursé) - float(prêt.montant)) * 0.9 * (2800 if prêt.devise == "USD" else 1)
                devise_pret = prêt.devise
                
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
                            prêt=prêt,
                            membre=membre,
                            montant=benefice_membre_usd if membre.contribution_mensuelle.devise == "USD" else benefice_membre,
                            devise=membre.contribution_mensuelle.devise  # Use loan currency
                        )
                    
                        print(f"{total_contributions_USD = } {total_contributions_CDF = } {contributions_membre_CDF = } {contributions_membre_USD = } {contributions_membre_CDF = } {montant_benefice = } {proportion =  } {benefice_membre = }")
                
                messages.success(request, "Le prêt a été approuvé et les bénéfices distribués avec succès.")
                return redirect("administrateurs:voir_prêt", prêt_id=prêt.pk)
            
        else:
            messages.error(request, "Mot de passe incorrect")
    
    context = {
        "form": PrêtsForm(instance=prêt),
        "transaction_form": TransactionsForm(),
        "numeros_categories": numeros_categories,
        "prêt": prêt
    }
    
    return render(request, "administrateurs/voir_prêt.html", context)

@login_required
def rejeter_prêt(request, prêt_id):
    prêt = get_object_or_404(Prêts, pk=prêt_id)

    prêt.statut = "Rejeté"
    prêt.date = timezone.now()
    prêt.save()
    messages.success(request, "Le prêt a été rejeté avec succès.")
    return redirect("administrateurs:voir_prêt", prêt_id=prêt.pk)
