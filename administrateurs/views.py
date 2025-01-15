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
from transactions.models import Transactions, Prets, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices, RetraitsObjectif, AnnulationObjectif, RemboursementsPret, RetraitsAdmin, BalanceAdmin

from .forms import AdministrateurForm
from membres.forms import MembresForm, ModifierMembresForm
from organisations.forms import OrganisationsForm
from transactions.forms import TransactionsForm, TypesPretForm, ContributionsForm, PretsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm
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
    solde_total_entreprise_cdf = Transactions.objects.filter(devise="CDF", type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    solde_total_entreprise_usd = Transactions.objects.filter(devise="USD", type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Solde de toutes les dettes
    total_montant_dettes_cdf = Prets.objects.filter(devise="CDF", statut__in=["Approuvé", "Remboursé", "Depassé"]).aggregate(total=Sum('montant_remboursé'))['total'] or 0
    total_montant_dettes_usd = Prets.objects.filter(devise="USD", statut__in=["Approuvé", "Remboursé", "Depassé"]).aggregate(total=Sum('montant_remboursé'))['total'] or 0
    
    total_prets_CDF = Prets.objects.filter(devise="CDF", statut__in=["Approuvé", "Remboursé", "Depassé"]).aggregate(total=Sum('montant'))['total'] or 0
    total_prets_USD = Prets.objects.filter(devise="USD", statut__in=["Approuvé", "Remboursé", "Depassé"]).aggregate(total=Sum('montant'))['total'] or 0

    total_montant_dettes_remboursees_CDF = RemboursementsPret.objects.filter(devise="CDF", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0
    total_montant_dettes_remboursees_USD = RemboursementsPret.objects.filter(devise="USD", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    # Calcul du solde total des dépôts sur les objectifs
    total_depots_objectifs_cdf = Objectifs.objects.filter(devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(Sum('montant'))['montant__sum'] or 0
    total_depots_objectifs_usd = Objectifs.objects.filter(devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(Sum('montant'))['montant__sum'] or 0

    # Calcul du solde total des retraits
    total_retraits_cdf = Transactions.objects.filter(devise="CDF", type="retrait", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits_usd = Transactions.objects.filter(devise="USD", type="retrait", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Calcul du solde Admin
    total_montant_admin_cdf = BalanceAdmin.objects.filter(devise="CDF").aggregate(Sum('montant'))['montant__sum'] or 0
    total_montant_admin_usd = BalanceAdmin.objects.filter(devise="USD").aggregate(Sum('montant'))['montant__sum'] or 0

    total_depot_inscription_CDF = Transactions.objects.filter(devise="CDF", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_inscription_USD = Transactions.objects.filter(devise="USD", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0
    
    # Calcul du solde total des retraits Admin
    total_retraits_admin_cdf = Transactions.objects.filter(devise="CDF", type="retrait_admin", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits_admin_usd = Transactions.objects.filter(devise="USD", type="retrait_admin", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Calcul du solde total des retraits_tout
    total_retraits_tout_cdf = Transactions.objects.filter(devise="CDF", type="retrait_tout", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits_tout_usd = Transactions.objects.filter(devise="USD", type="retrait_tout", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Calcul du solde total des qnnulations_objectif
    total_annulation_objectif_cdf = AnnulationObjectif.objects.filter(devise="CDF", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0
    total_annulation_objectif_usd = AnnulationObjectif.objects.filter(devise="USD", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    # Nombre total de membres, organisations et agents
    nombre_membres = Membres.objects.count()
    nombre_organisations = Organisations.objects.count()
    nombre_agents = Agents.objects.count()

    transactions = Transactions.objects.all().order_by("-date")
    objectifs = Objectifs.objects.filter(statut__in=["En cours", "Atteint", "Epuisé"])

    demandes_pret = Prets.objects.filter(statut="En attente")
    demandes_inscription = DepotsInscription.objects.filter(statut="En attente")
    demandes_retrait = Retraits.objects.filter(statut="En attente")
    demandes_retrait_tout = Transactions.objects.filter(statut="Demande", type="retrait_tout")
    demandes_annulation_objectif = AnnulationObjectif.objects.filter(statut="En attente")
    demandes_retrait_objectif = RetraitsObjectif.objects.filter(statut="En attente")
    
    context = {
        'solde_total_entreprise_cdf': float(solde_total_entreprise_cdf) + float(total_depot_inscription_CDF) + float(total_montant_dettes_remboursees_CDF) + float(total_annulation_objectif_cdf)/10 - (float(total_prets_CDF) + float(total_retraits_cdf) + float(total_retraits_tout_cdf) + float(total_retraits_admin_cdf)),
        'solde_total_entreprise_usd': float(solde_total_entreprise_usd) + float(total_depot_inscription_USD) + float(total_montant_dettes_remboursees_USD) + float(total_annulation_objectif_usd)/10 - (float(total_prets_USD) + float(total_retraits_usd) + float(total_retraits_tout_usd) + float(total_retraits_admin_usd)),
        'total_dettes_cdf': float(total_montant_dettes_cdf) - float(total_montant_dettes_remboursees_CDF),
        'total_dettes_usd': float(total_montant_dettes_usd) - float(total_montant_dettes_remboursees_USD),
        'total_depots_objectifs_cdf': total_depots_objectifs_cdf,
        'total_depots_objectifs_usd': total_depots_objectifs_usd,
        'total_benefices_cdf': float(total_montant_admin_cdf) - float(total_retraits_admin_cdf),
        'total_benefices_usd': float(total_montant_admin_usd) - float(total_retraits_admin_usd),
        'nombre_membres': nombre_membres,
        'nombre_organisations': nombre_organisations,
        'nombre_agents': nombre_agents,
        "transactions": transactions,
        "demandes_pret": demandes_pret,
        "demandes_inscription": demandes_inscription,
        "demandes_retrait": demandes_retrait,
        "demandes_retrait_objectif": demandes_retrait_objectif,
        "demandes_retrait_tout": demandes_retrait_tout,
        "demandes_annulation_objectif": demandes_annulation_objectif,
        "objectifs": objectifs,
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
            messages.success(request, "Vos informations ont été mises à jour avec succès")
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
    
    membres_actifs = Membres.objects.filter().order_by("-date_creation")

    for membre in membres:
        membre.solde_objecticfs = float(Objectifs.objects.filter(membre=membre, devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0) / 2800 + \
                                float(Objectifs.objects.filter(membre=membre, devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0)
        
        membre.solde_contributions = Transactions.objects.filter(membre=membre, devise="CDF" if membre.contribution_mensuelle.devise == "CDF" else "USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
        membre.benefice_membre = float(Benefices.objects.filter(membre=membre).aggregate(Sum('montant'))['montant__sum'] or 0) - float(Transactions.objects.filter(membre=membre, statut="Approuvé", type="retrait").aggregate(Sum('montant'))['montant__sum'] or 0)
        
        if total_contributions_CDF > 0:  # Avoid ZeroDivisionError
            membre.pourcentage = float(membre.solde_contributions * (2800 if membre.contribution_mensuelle.devise == "USD" else 1) / total_contributions_CDF) * 100

        membre.dette = Prets.objects.filter(transaction__membre=membre, statut="Approuvé").first()
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

            messages.success(request, "Le membre a été créé avec succès")
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
            messages.success(request, "Le membre a été modifié avec succès")
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
            messages.success(request, "Le membre a été modifié avec succès")
            return redirect("administrateurs:membres")
        
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire")
    
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
    messages.success(request, "Le membre a été supprimé avec succès")
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

                BalanceAdmin.objects.create(
                    montant=depot.montant,
                    devise=depot.devise,
                    type="depot_inscription"
                )

            membre.save()
            depot.save()

            messages.success(request, "Le membre a été accepté avec succès")
            return redirect("administrateurs:home")
        
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire")
            return redirect("administrateurs:accepter_membre", membre_id)

@login_required
@verifier_admin
def refuser_membre(request, membre_id):
    membre = get_object_or_404(Membres, pk=membre_id)

    depot=DepotsInscription.objects.get(membre=membre)
    depot.statut = "Rejeté"
    depot.save()
    membre.status = False
    membre.save()

    messages.success(request, "Le membre a été refusé avec succès")
    return redirect("administrateurs:home")

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
        agent.total_annulation_objectif_usd = 0
        agent.total_retrait_tout = 0


        for devise, rate in {"CDF": 2800, "USD": 1}.items():  # Replace with your dynamic rate fetching
            agent.total_depot_inscription_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="depot_inscription", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_contributions_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_prets_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="pret", statut__in=["Approuvé", "Remboursé", "Depassé"]).aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_remboursements_prets_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="remboursement_pret", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_retraits_usd += float(Transactions.objects.filter(agent=agent, devise=devise, type="retrait", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_objectifs_usd += float(Transactions.objects.filter(agent=agent, devise=devise, statut="Approuvé", type="depot_objectif").aggregate(Sum('montant'))['montant__sum'] or 0) / rate # Correct this line
            agent.total_annulation_objectif_usd += float(AnnulationObjectif.objects.filter(transaction__agent=agent, devise=devise, statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate
            agent.total_retrait_tout += float(Transactions.objects.filter(agent=agent, devise=devise, type="retrait_tout", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0) / rate

        agent.total_transactions_usd = (
            agent.total_contributions_usd -
            agent.total_prets_usd +
            agent.total_remboursements_prets_usd -
            agent.total_retraits_usd +
            agent.total_depot_inscription_usd +
            agent.total_annulation_objectif_usd / 10 -
            agent.total_retrait_tout
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

            messages.success(request, "L'agent a été créé avec succès")
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
            messages.success(request, "L'agent a été modifié avec succès")
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
            messages.success(request, "L'agent a été modifié avec succès")
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
    NumerosAgent.objects.filter(agent=agent).delete()
    agent.delete()
    messages.success(request, "L'agent a été supprimé avec succès")
    return redirect("administrateurs:agents")

@login_required
@verifier_admin
def objectifs(request):
    solde_objectifs_CDF = Objectifs.objects.filter(devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0
    solde_objectifs_USD = Objectifs.objects.filter(devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0

    objectifs = Objectifs.objects.filter(statut__in=["En cours", "Atteint", "Epuisé"]).order_by("-date_debut")

    for objectif in objectifs:
        objectif.pourcentage = float(objectif.montant / objectif.montant_cible ) * 100
        if timezone.now().date() > objectif.date_fin:
            objectif.statut = "Epuisé"
            objectif.save()

    context = {
        "objectifs": objectifs,
        "solde_objectifs_CDF": solde_objectifs_CDF,
        "solde_objectifs_USD": solde_objectifs_USD
    }
    return render(request, "administrateurs/objectifs.html", context)

@login_required
@verifier_admin
def retrait(request):
    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    montant_retrait = float(RetraitsAdmin.objects.filter(transaction__statut="Approuvé", devise="CDF").aggregate(total=Sum('montant'))['total'] or 0) + float(RetraitsAdmin.objects.filter(transaction__statut="Approuvé", devise="USD").aggregate(total=Sum('montant'))['total'] or 0)*2800
    max = float(BalanceAdmin.objects.filter(devise="CDF").aggregate(total=Sum('montant'))['total'] or 0) + float(BalanceAdmin.objects.filter(devise="USD").aggregate(total=Sum('montant'))['total'] or 0)*2800 - montant_retrait

    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                transaction = transaction_form.save(commit=False)
                
                if not Transactions.objects.filter(admin=request.user.admin, type="retrait_admin", statut="En attente").exists():
                    if transaction.montant > 0 and transaction.montant <= max / (1 if transaction.devise == "CDF" else 2800):
                        transaction.admin = request.user.admin
                        transaction.agent = transaction.numero_agent.agent
                        transaction.type = "retrait_admin"
                        transaction.statut = "En attente"

                        transaction.save()

                        RetraitsAdmin.objects.create(
                            montant=transaction.montant,
                            devise=transaction.devise,
                            transaction=transaction
                        )

                        messages.success(request, "La demande de retrait a été soumise avec succès")
                        return redirect("administrateurs:home")
                    
                    else:
                        messages.error(request, "Montant insuffisant")
                
                else:
                    messages.error(request, "Vous avez déjà une demande de retrait en attente")

            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")

        else:
            messages.error(request, "Mot de passe incorrect")
    
    context = {
        "form": TransactionsForm(),
        "numeros_categories": numeros_categories,
        "max_CDF": max,
        "max_USD": max / 2800,
        "transactions": Transactions.objects.filter(type="retrait_admin").order_by("-date")
    }

    return render(request, "administrateurs/retrait.html", context)

# Vue pour la page de gestion des transactions
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

@login_required
@verifier_admin
def prets(request):
    prets = Prets.objects.all().order_by("-date_remboursement")

    for pret in prets:
        if pret.statut == "Approuvé" and timezone.now() > pret.date_remboursement:
            pret.montant_remboursé += 5 * (2800 if pret.devise == "CDF" else 1)
            pret.statut = "Depassé"
            pret.save()
            
    context = {"prets": prets}
    return render(request, "administrateurs/prets.html", context)

@login_required
@verifier_admin
def voir_pret(request, pret_id):
    pret = get_object_or_404(Prets, pk=pret_id)
    pret.membre.capital = Contributions.objects.filter(transaction__membre=pret.membre, mois=pret.membre.mois_contribution, devise=pret.membre.contribution_mensuelle.devise, statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0
    pret.membre.capital_total = Contributions.objects.filter(transaction__membre=pret.membre, devise=pret.membre.contribution_mensuelle.devise, statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))
    
    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST, instance=pret.transaction)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                pret.date_approbation = timezone.now()
                pret.administrateur = request.user.admin
                pret.statut = "Approuvé"

                transaction = transaction_form.save(commit=False)

                transaction.membre = pret.membre
                transaction.agent = transaction.numero_agent.agent

                transaction.montant = pret.montant
                transaction.devise = pret.devise

                transaction.statut = "En attente"

                transaction.save()
                pret.save()
            
                messages.success(request, "Le pret a été approuvé avec succès")
                return redirect("administrateurs:home")
            
        else:
            messages.error(request, "Mot de passe incorrect")
    
    context = {
        "form": PretsForm(instance=pret),
        "transaction_form": TransactionsForm(instance=pret.transaction),
        "numeros_categories": numeros_categories,
        "pret": pret
    }
    
    return render(request, "administrateurs/voir_pret.html", context)

@login_required
@verifier_admin
def rejeter_pret(request, pret_id):
    pret = get_object_or_404(Prets, pk=pret_id)

    pret.statut = pret.transaction.statut = "Rejeté"
    pret.date = timezone.now()

    pret.transaction.save()
    pret.save()
    messages.success(request, "Le pret a été rejeté avec succès")
    return redirect("administrateurs:home")

@login_required
@verifier_admin
def voir_retrait_objectif(request, retrait_objectif_id):
    retrait_objectif = get_object_or_404(RetraitsObjectif, pk=retrait_objectif_id)
    membre = retrait_objectif.membre

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST, instance=retrait_objectif.transaction)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                retrait_objectif.date_approbation = timezone.now()
                retrait_objectif.statut = "Approuvé"

                transaction = transaction_form.save(commit=False)

                transaction.membre = membre
                transaction.agent = transaction.numero_agent.agent
                transaction.statut = "En attente"

                transaction.save()
                retrait_objectif.save()
                messages.success(request, "Le retrait a été approuvé avec succès")
                return redirect("administrateurs:home")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")
        else:
            messages.error(request, "Mot de passe incorrect")

    context = {
        "form": TransactionsForm(instance=retrait_objectif.transaction),
        "numeros_categories": numeros_categories,
        "retrait_objectif": retrait_objectif,
        "membre": membre,
        "pourcentage_retrait": retrait_objectif.frais * 100,
        "frais_retrait": retrait_objectif.montant * retrait_objectif.frais,
        "montant_à_retirer": retrait_objectif.transaction.montant
    }

    return render(request, "administrateurs/voir_retrait_objectif.html", context)

@login_required
@verifier_admin
def rejeter_retrait_objectif(request, retrait_objectif_id):
    retrait_objectif = get_object_or_404(RetraitsObjectif, pk=retrait_objectif_id)
    retrait_objectif.statut = retrait_objectif.transaction.statut = "Rejeté"
    retrait_objectif.date = timezone.now()

    retrait_objectif.transaction.save()
    retrait_objectif.save()
    messages.success(request, "Le retrait a été rejeté avec succès")
    return redirect("administrateurs:home")

@login_required
@verifier_admin
def voir_annulation_objectif(request, annulation_objectif_id):
    annulation_objectif = get_object_or_404(AnnulationObjectif, pk=annulation_objectif_id)
    membre = annulation_objectif.membre

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST, instance=annulation_objectif.transaction)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                annulation_objectif.date_approbation = timezone.now()
                annulation_objectif.statut = "Approuvé"

                transaction = transaction_form.save(commit=False)

                transaction.membre = membre
                transaction.agent = transaction.numero_agent.agent
                transaction.statut = "En attente"

                transaction.save()
                annulation_objectif.save()
                messages.success(request, "L'annulation a été approuvée avec succès")
                return redirect("administrateurs:home")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")
        else:
            messages.error(request, "Mot de passe incorrect")

    context = {
        "form": TransactionsForm(instance=annulation_objectif.transaction),
        "numeros_categories": numeros_categories,
        "annulation_objectif": annulation_objectif,
        "membre": membre,
        "pourcentage_retrait": annulation_objectif.frais * 100,
        "frais_retrait": annulation_objectif.montant * annulation_objectif.frais,
        "montant_à_retirer": annulation_objectif.transaction.montant
    }

    return render(request, "administrateurs/voir_annulation_objectif.html", context)

@login_required
@verifier_admin
def rejeter_annulation_objectif(request, annulation_objectif_id):
    annulation_objectif = get_object_or_404(AnnulationObjectif, pk=annulation_objectif_id)
    annulation_objectif.statut = annulation_objectif.transaction.statut = "Rejeté"
    annulation_objectif.date = timezone.now()

    annulation_objectif.transaction.save()
    annulation_objectif.save()
    messages.success(request, "L'annulation a été rejetée avec succès")
    return redirect("administrateurs:home")

@login_required
@verifier_admin
def voir_retrait(request, retrait_id):
    retrait = get_object_or_404(Retraits, pk=retrait_id)
    membre = retrait.membre

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST, instance=retrait.transaction)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                retrait.date_approbation = timezone.now()
                retrait.statut = "Approuvé"

                transaction = transaction_form.save(commit=False)

                transaction.membre = membre
                transaction.agent = transaction.numero_agent.agent
                transaction.statut = "En attente"

                transaction.save()
                retrait.save()
                messages.success(request, "Le retrait a été approuvé avec succès")
                return redirect("administrateurs:home")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")
        else:
            messages.error(request, "Mot de passe incorrect")
    
    context = {
        "form": TransactionsForm(instance=retrait.transaction),
        "numeros_categories": numeros_categories,
        "retrait": retrait,
        "pourcentage_retrait": retrait.frais * 100,
        "frais_retrait": retrait.montant * retrait.frais,
        "montant_à_retirer": retrait.transaction.montant,
        "membre": membre
    }

    return render(request, "administrateurs/voir_retrait.html", context)

@login_required
@verifier_admin
def rejeter_retrait(request, retrait_id):
    retrait = get_object_or_404(Retraits, pk=retrait_id)
    retrait.statut = retrait.transaction.statut = "Rejeté"
    retrait.date = timezone.now()

    retrait.transaction.save()
    retrait.save()
    messages.success(request, "Le retrait a été rejeté avec succès")
    return redirect("administrateurs:home")

@login_required
@verifier_admin
def demande_retrait_tout(request, retrait_id):
    retrait = get_object_or_404(Transactions, pk=retrait_id, type="retrait_tout")
    membre = retrait.membre

    objectifs = Objectifs.objects.filter(membre=membre)

    montant_contributions = float(Transactions.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0)
    montant_objectifs = (float(Objectifs.objects.filter(membre=membre, devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(Sum('montant'))['montant__sum'] or 0) + float(Objectifs.objects.filter(membre=membre, devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(Sum('montant'))['montant__sum'] or 0) * 2800) * (1/2800 if membre.contribution_mensuelle.devise == "USD" else 1)
    montant_benefices = float(Benefices.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, statut=True).aggregate(Sum('montant'))['montant__sum'] or 0) - float(Retraits.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0)

    montant_total = montant_contributions + montant_objectifs + montant_benefices

    montant_total_USD = montant_total / 2800 if membre.contribution_mensuelle.devise == "CDF" else montant_total
    
    if montant_total_USD > 0 and montant_total_USD <= 10: frais = 0.085
    elif montant_total_USD > 10 and montant_total_USD <= 20: frais = 0.058
    elif montant_total_USD > 20 and montant_total_USD <= 50: frais = 0.0295
    elif montant_total_USD > 50 and montant_total_USD <= 400: frais = 0.0175
    elif montant_total_USD > 400: frais = 0.01

    frais = 0.1

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        mot_de_passe = request.POST.get("password")
        transaction_form = TransactionsForm(request.POST, instance=retrait)

        if check_password(mot_de_passe, request.user.password):
            if transaction_form.is_valid():
                retrait = transaction_form.save(commit=False)

                retrait.agent = retrait.numero_agent.agent
                retrait.montant = montant_total * (1 - frais)

                retrait.date_approbation = timezone.now()
                retrait.administrateur = request.user.admin

                depot_inscription = DepotsInscription.objects.get(membre=membre)
                # depot_inscription.statut = "En attente"
                depot_inscription.transaction = None
                depot_inscription.montant = 10
                depot_inscription.save()

                retrait.statut = "En attente"
                retrait.save()

                messages.success(request, "Le retrait a été approuvé avec succès")
                return redirect("administrateurs:home")

            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")
                print(transaction_form.errors)
        
        else:
            messages.error(request, "Mot de passe incorrect")
    
    context = {
        "form": TransactionsForm(instance=retrait),
        "numeros_categories": numeros_categories,
        "retrait": retrait,
        "membre": membre,
        "montant_contributions": montant_contributions,
        "objectifs": objectifs,
        "montant_objectifs": montant_objectifs,
        "montant_benefices": montant_benefices,
        "montant_total": montant_total,
        "montant_à_retirer": montant_total * (1 - frais),
        "pourcentage_retrait": frais * 100,
        "frais_retrait": frais * montant_total
    }

    return render(request, "administrateurs/voir_retrait_tout.html", context)

@login_required
@verifier_admin
def refuser_retrait_tout(request, retrait_id):
    retrait = get_object_or_404(Transactions, pk=retrait_id, type="retrait_tout")
    retrait.statut = "Rejeté"
    retrait.date = timezone.now()
    retrait.save()
    messages.success(request, "Le retrait a été rejeté avec succès")
    return redirect("administrateurs:home")
