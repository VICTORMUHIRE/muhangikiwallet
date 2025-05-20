from decimal import Decimal
import json
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.template.defaultfilters import slugify
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from membres.service import benefices_actuelle, investissement_actuelle, rechargerCompteService

from .models import Membres
from .forms import MembresForm, ModifierMembresForm
from agents.models import Agents, NumerosAgent
from administrateurs.models import Users, NumerosCompte,Villes, Communes, Quartiers, Avenues
from organisations.models import Organisations
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from transactions.models import BalanceAdmin, RetraitContributions, Solde, Transactions, Prets, RemboursementsPret, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices, RetraitsObjectif, AnnulationObjectif
from transactions.forms import ContributionsForm, PretsForm, SoldeForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm, TypesPretForm, TransactionsForm, DepotsObjectifForm
from datetime import datetime, timedelta
from django.utils import timezone
from functools import wraps
from random import randint
from django.http import JsonResponse
from django.db import transaction as db_transaction

def verifier_membre(func):
    def verify(request, *args, **kwargs):
        if request.user.is_membre():
            if request.user.membre.status and Transactions.objects.filter(membre=request.user.membre, type="depot_inscription", statut="Approuvé").exists():
                return func(request, *args, **kwargs)
            else : return redirect("membres:statut")

        else: return redirect("index")

    return wraps(func)(verify)

def get_villes(request):
    province_id = request.GET.get('province_id')
    villes = Villes.objects.filter(province_id=province_id).values('id', 'nom', 'type')
    return JsonResponse(list(villes), safe=False)

def get_communes(request):
    ville_id = request.GET.get('ville_id')
    communes = Communes.objects.filter(ville_id=ville_id).values('id', 'nom')
    return JsonResponse(list(communes), safe=False)

def get_quartiers(request):
    commune_id = request.GET.get('commune_id')
    quartiers = Quartiers.objects.filter(commune_id=commune_id).values('id', 'nom')
    return JsonResponse(list(quartiers), safe=False)

def get_avenues(request):
    quartier_id = request.GET.get('quartier_id')
    avenues = Avenues.objects.filter(quartier_id=quartier_id).values('id', 'nom')
    return JsonResponse(list(avenues), safe=False)

# Vue pour la page de statut des membres
@login_required
def statut(request):
    depot_inscription = DepotsInscription.objects.filter(membre=request.user.membre).first()

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == 'POST':
        form = TransactionsForm(request.POST, request.FILES)
        membre_form = ModifierMembresForm(request.POST, request.FILES, instance=request.user.membre)       
        
        mot_de_passe = request.POST.get('mot_de_passe')

        if form.is_valid():
            if check_password(mot_de_passe, request.user.password):
                transaction = form.save(commit=False)

                transaction.devise = depot_inscription.devise
                transaction.montant = depot_inscription.montant
                transaction.agent = transaction.numero_agent.agent
                transaction.membre=request.user.membre
                transaction.type="depot_inscription"
                transaction.statut = "En attente"

                depot_inscription.date = timezone.now()
                depot_inscription.transaction = transaction
                
                transaction.save()
                depot_inscription.save()

                messages.success(request, "Votre dépot d'inscription a été soumise avec succès !")
                return redirect('membres:home')
            
            else:
                messages.error(request, "Mot de passe incorrect")

        elif membre_form.is_valid():
            membre_form.save()

            depot_inscription.statut = "En attente"
            depot_inscription.save()

            messages.success(request, "Vos informations ont été modifiées avec succès !")
            return redirect('membres:home')
        
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire")

    else:
        form = TransactionsForm(initial={"montant": depot_inscription.montant, "devise": depot_inscription.devise})
        membre_form = ModifierMembresForm(instance=request.user.membre)

    context = {
        'form': form,
        'membre_form': membre_form,
        'reseaux': reseaux,
        'numeros_categories': numeros_categories,
        "depot_inscription": depot_inscription
    }

    return render(request, 'membres/statut.html', context) # Pass the form to the template

# Vue pour la page d'inscription des membres
def inscription(request):
    if request.user.is_authenticated:
        return redirect("membres:home")

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
            
            membre.mois_contribution = timezone.now().replace(day=15)
            membre.save()

            DepotsInscription.objects.create(membre=membre)

            login(request, membre.user)
            return redirect("login")
        
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire")
            # fs = FileSystemStorage()
            # for name, file in request.FILES.items():
            #     filename = fs.save("{name}/" + file.name, file)

    else: form = MembresForm()
    
    return render(request, "membres/inscription.html", {"form": form})

# Vue pour la page de changement de mot de passe des membres
def password_reset(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Votre mot de passe a été mis à jour avec succès")
            return redirect("muhangiki_wallet:login")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "membres/password_reset.html", {"form": form})

# Vue pour les termes et conditions
def termes_et_conditions(request):
    return render(request, "membres/termes_et_conditions.html")

# Vue Accueil des membres
@login_required
@verifier_membre
def home(request):
    membre = request.user.membre

    compte_usd = membre.compte_USD
    compte_cdf = membre.compte_CDF

    objectifs = Objectifs.objects.filter(membre=membre).order_by("-date_creation")

    solde_CDF = investissement_actuelle(membre, "CDF")
    solde_USD = investissement_actuelle(membre, "USD")

    total_prets_CDF = Prets.objects.filter(transaction__membre=membre, devise="CDF", transaction__statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0
    total_prets_USD = Prets.objects.filter(transaction__membre=membre, devise="USD", transaction__statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0

    total_prets_rembourses_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_rembourses_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_objectif_CDF = Objectifs.objects.filter(membre=membre, devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Objectifs.objects.filter(membre=membre, devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0
    
    benefices_CDF = benefices_actuelle(membre, "CDF")
    benefices_USD = benefices_actuelle(membre, "USD")

    transactions = Transactions.objects.filter(membre=membre).order_by("-date")

    form = SoldeForm()

    context = {
        "membre": membre,
        "compte_usd":compte_usd.solde,
        "compte_cdf":compte_cdf.solde,
        "objectifs": objectifs,
        "total_prets_CDF": float(total_prets_CDF) - float(total_prets_rembourses_CDF),
        "total_prets_USD": float(total_prets_USD) - float(total_prets_rembourses_USD),
        "total_depot_objectif_CDF": total_depot_objectif_CDF,
        "total_depot_objectif_USD": total_depot_objectif_USD,
        "solde_CDF": solde_CDF,
        "solde_USD": solde_USD,
        "transactions": transactions,
        "benefices_CDF": benefices_CDF,
        "benefices_USD": benefices_USD,
        "form":form,
    }

    return render(request, "membres/home.html", context)

# Vue pour la page de profil du membre
@login_required
@verifier_membre
def profile(request):
    membre = request.user.membre

    if request.method == 'POST':
        if 'nouvellePhoto' in request.FILES: # Check if a new photo was uploaded
            # Handle photo upload manually
            photo_file = request.FILES['nouvellePhoto']
            fs = FileSystemStorage()
            filename = fs.save("photo_profile/" + photo_file.name, photo_file)
            uploaded_file_url = fs.url(filename)

            membre = request.user.membre

            if fs.exists(str(settings.BASE_DIR) + membre.photo_passport.name):
                fs.delete(str(settings.BASE_DIR) + membre.photo_passport.name)

            membre.photo_passport = uploaded_file_url  # Update the photo_passport field
            membre.save()

            messages.success(request, 'Photo de profil mise à jour avec succès.')
            return redirect('membres:profile')
    else:
        form = ModifierMembresForm(instance=membre)

    context = {
        "form": form
    }
    return render(request, "membres/profile.html", context)

# Vue pour la page de dépôt de contribution du membre
@login_required
@verifier_membre
def contributions(request):
    membre = request.user.membre
    solde_contribution_CDF = investissement_actuelle(membre, "CDF")
    solde_contribution_USD = investissement_actuelle(membre, "USD")

    contributions = Contributions.objects.filter(transaction__membre=request.user.membre).order_by('-date')

    if request.method == 'POST':
        form = TransactionsForm(request.POST)
        mot_de_passe = request.POST.get('mot_de_passe')

        if check_password(mot_de_passe, request.user.password):
            if form.is_valid():
                montant = form.cleaned_data['montant']
                devise = form.cleaned_data['devise']

                # Vérifier le solde selon la devise
                compte = membre.compte_USD if devise == "USD" else membre.compte_CDF

                if montant <= compte.solde and montant > 0:
                    with db_transaction.atomic(): 
                        # Débit du compte
                        compte.solde -= montant

                        # Création de la transaction
                        transaction = form.save(commit=False)
                        transaction.devise = devise
                        transaction.type = "contribution"
                        transaction.statut = "Approuvé"  # ou "En attente"
                        transaction.membre = membre
                        transaction.save()

                        # Création de la contribution liée
                        Contributions.objects.create(
                            transaction=transaction,
                            montant=montant,
                            devise=devise,
                            mois=membre.mois_contribution,
                            statut="Approuvé"  # ou "En attente"
                        )
                        compte.save()

                        messages.success(request, "Contribution enregistrée avec succès.")
                        return redirect("membres:contributions")
                else:
                    messages.error(request, "Solde insuffisant ou montant invalide.")
            else:
                messages.error(request, "Formulaire invalide.")
        else:
            messages.error(request, "Mot de passe incorrect.")
    else:
        form = TransactionsForm()



    context = {
        "membre": membre,
        "form": form,
        "contributions": contributions,
        "solde_contribution_CDF": solde_contribution_CDF,
        "solde_contribution_USD": solde_contribution_USD,
    }
    return render(request, "membres/contributions.html", context)


@login_required
@verifier_membre
def demande_pret(request):
    types_pret = TypesPret.objects.all()
    demandes_pret = Prets.objects.filter(membre=request.user.membre).order_by("-date_demande")

    taux_de_change = 2800
    membre = request.user.membre

    solde_contribution_CDF = investissement_actuelle(membre, "CDF")
    solde_contribution_USD = investissement_actuelle(membre, "USD")

    max_possible_cdf = solde_contribution_CDF + (solde_contribution_USD * taux_de_change)
    max_possible_usd = solde_contribution_USD + (solde_contribution_CDF / taux_de_change)

    if request.method == "POST":
        form = PretsForm(request.POST)

        if form.is_valid():
            mot_de_passe = request.POST.get('mot_de_passe')
            mode_payement = request.POST.get('mode_payement', 'hebdomadaire')

            if check_password(mot_de_passe, request.user.password):
                pret = form.save(commit=False)
                pret.membre = membre
                type_pret = pret.type_pret
                nom_pret = type_pret.nom.lower()

                montant = float(pret.montant)
                montant_cdf = montant if pret.devise == "CDF" else montant * taux_de_change
                solde_total_contribution = solde_contribution_CDF + (solde_contribution_USD * taux_de_change)
                anciennete = (timezone.now().date() - membre.date_creation.date()).days

                # Vérification spécifique pour chaque type de prêt
                if nom_pret == "prêts express":
                    if anciennete < 60:
                        messages.error(request, "Vous devez avoir au moins 2 mois dans le système pour ce type de prêt.")
                        return redirect("membres:demande_pret")

                    if montant_cdf > max_possible_cdf:
                        messages.error(request, "Le montant demandé dépasse vos contributions.")
                        return redirect("membres:demande_pret")

                elif nom_pret == "prêts commercial starter":
                    if solde_total_contribution < type_pret.investissement_min * taux_de_change:
                        messages.error(request, f"Vous devez avoir au moins {type_pret.investissement_min}$ de contributions totales.")
                        return redirect("membres:demande_pret")

                    if montant < type_pret.montant_min or montant > type_pret.montant_max:
                        messages.error(request, "Le montant demandé doit être entre les limites définies pour ce type de prêt.")
                        return redirect("membres:demande_pret")

                elif nom_pret == "prêts commercial pro":
                    nombre_contributions = Transactions.objects.filter(membre=membre, statut="Approuvé", type="contribution").count()

                    if anciennete < 90:
                        messages.error(request, "Vous devez avoir au moins 3 mois dans le système pour ce prêt.")
                        return redirect("membres:demande_pret")

                    if nombre_contributions < 5:
                        messages.error(request, "Vous devez avoir au moins 5 contributions approuvées.")
                        return redirect("membres:demande_pret")

                    if solde_total_contribution < type_pret.investissement_min * taux_de_change:
                        messages.error(request, "Vous devez avoir au moins 200$ de contributions totales.")
                        return redirect("membres:demande_pret")

                    if montant < type_pret.montant_min or montant > type_pret.montant_max:
                        messages.error(request, "Le montant demandé doit respecter les limites définies pour ce type de prêt.")
                        return redirect("membres:demande_pret")

                else:
                    messages.error(request, "Type de prêt invalide ou non pris en charge.")
                    return redirect("membres:demande_pret")

                # Vérifications globales communes
                if Transactions.objects.filter(membre=membre, type="retrait_tout", statut__in=["En attente", "Demande"]).exists():
                    messages.error(request, "Vous avez une demande de retrait total en cours.")
                    return redirect("membres:demande_pret")

                if Prets.objects.filter(membre=membre, statut="En attente").exists():
                    messages.error(request, "Vous avez déjà une demande de prêt en attente.")
                    return redirect("membres:demande_pret")

                if Prets.objects.filter(membre=membre, statut__in=["Approuvé", "Depassé"]).exists():
                    messages.error(request, "Vous avez déjà un prêt approuvé ou dépassé.")
                    return redirect("membres:demande_pret")

                # Calcul du montant à rembourser
                taux = float(type_pret.taux_interet) / 100
                delai = int(type_pret.delai_remboursement)
                montant_payer = montant + (montant * taux * delai)

                if mode_payement == "mensuel":
                    montant_remboursé_tranche = montant_payer / delai
                    pret.date_remboursement = timezone.now() + timedelta(days=30 * delai)
                elif mode_payement == "hebdomadaire":
                    montant_remboursé_tranche = montant_payer / (delai * 4)
                    pret.date_remboursement = timezone.now() + timedelta(days=7 * delai * 4)
                else:
                    messages.error(request, "Mode de paiement invalide.")
                    return redirect("membres:demande_pret")


                # Sauvegarde finale
                pret.mode_payement = mode_payement
                pret.devise = pret.devise
                pret.montant_payer = montant_payer
                pret.montant_remboursé = montant_remboursé_tranche

                transaction = Transactions.objects.create(
                    membre=membre,
                    montant=montant,
                    devise=pret.devise,
                    type="pret"
                )
                pret.transaction = transaction
                pret.save()

                messages.success(request, 'Votre demande de prêt a été soumise avec succès.')
                return redirect("membres:demande_pret")

            else:
                messages.error(request, 'Mot de passe incorrect.')
        else:
            messages.error(request, 'Formulaire invalide.')
    else:
        form = PretsForm()

    context = {
        "form": form,
        "types_pret": types_pret,
        "demandes_pret": demandes_pret,
        "taux_change": taux_de_change,
        "max_possible_cdf": max_possible_cdf,
        "max_possible_usd": max_possible_usd,
    }

    return render(request, "membres/demande_pret.html", context)

# Vue pour la page de remboursement du pret du membre
@login_required
@verifier_membre
def rembourser_pret(request, transaction_id):
    pret = get_object_or_404(
        Prets,
        transaction=get_object_or_404(
            Transactions,
            pk=transaction_id,
            membre=request.user.membre,
            type="pret",
            statut="Approuvé"
        ),
        statut__in=["Approuvé", "Depassé","Remboursé"]
    )

    if pret.statut == "Remboursé":
        messages.warning(request, "Ce prêt est déjà totalement remboursé.")
        return redirect("membres:demande_pret")

    compte_membre = pret.membre.compte_USD if pret.devise == "USD" else pret.membre.compte_CDF
    montant_restant = pret.montant_remboursé - pret.solde_remboursé

    if request.method == "POST":
        form = TransactionsForm(request.POST, request.FILES)
        mot_de_passe = request.POST.get('password')

        if form.is_valid():
            if not check_password(mot_de_passe, request.user.password):
                messages.error(request, "Mot de passe incorrect. Veuillez réessayer.")
                return redirect(request.path)

            montant = form.cleaned_data['montant']

            # Validation du montant
            if montant <= 0 or montant > montant_restant or montant > compte_membre.solde:
                messages.error(request, "Montant invalide ou solde insuffisant.")
                return redirect(request.path)

            # Vérifier s'il n'existe pas déjà une transaction en attente (facultatif maintenant)
            if Transactions.objects.filter(
                membre=request.user.membre,
                type="remboursement_pret",
                statut="En attente"
            ).exists():
                messages.error(request, "Une demande de remboursement est déjà en attente.")
                return redirect(request.path)

            # Créer et enregistrer la transaction
            transaction = form.save(commit=False)
            transaction.membre = request.user.membre
            transaction.type = "remboursement_pret"
            transaction.statut = "Approuvé"
            transaction.description = f"Remboursement automatique du prêt N°{pret.pk}"
            transaction.date_approbation = timezone.now()
            transaction.save()

            # Créer l'objet de remboursement
            RemboursementsPret.objects.create(
                pret=pret,
                montant=montant,
                devise=pret.devise,
                transaction=transaction,
                statut="Remboursé"
            )

            # Mise à jour du prêt
            pret.solde_remboursé += montant
            if pret.solde_remboursé >= pret.montant_remboursé:
                pret.solde_remboursé = pret.montant_remboursé  # éviter dépassement
                if pret.statut == "Depassé":
                    BalanceAdmin.objects.create(
                        montant=5 * (2800 if pret.devise == "CDF" else 1),
                        devise=pret.devise,
                        type="remboursement_pret"
                    )
                pret.statut = "Remboursé"
                pret.date_remboursement = timezone.now()
                pret.transaction.save()
            pret.save()

            # Mise à jour du compte
            compte_membre.solde -= montant
            compte_membre.save()

            messages.success(request, "Remboursement effectué avec succès !")
            return redirect("membres:demande_pret")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = TransactionsForm()

    context = {
        "form": form,
        "pret": pret,
        "montant_restant": montant_restant,
    }

    return render(request, "membres/rembourser_pret.html", context)

# Vue pour la page de gestion des objectifs du membre
@login_required
@verifier_membre
def objectifs(request):
    if request.method == "POST":
        form = ObjectifsForm(request.POST)
        if form.is_valid():
            objectif = form.save(commit=False)

            if True or not Objectifs.objects.filter(membre=request.user.membre, nom=objectif.nom, statut__in=["En cours", "Atteint", "Epuisé"]).exists():
                if objectif.montant_cible > 0:
                    if objectif.date_debut < objectif.date_fin:
                        objectif.membre = request.user.membre
                        form.save()
                        messages.success(request, "Votre objectif a été créé avec succès")
                    
                    else:
                        messages.error(request, 'La date de fin doit être supérieure à la date de début')
                else:
                    messages.error(request, 'Montant invalide, veuillez réessayer')
            else:
                messages.error(request, "Cet objectif existe déjà")

        else: messages.error(request, "Veuillez corriger les erreurs dans le formulaire")

        return redirect("membres:objectifs")
    
    else: form = ObjectifsForm(initial={"date_debut": timezone.now(), "date_fin": timezone.now() + timedelta(days=30)})
    
    solde_objectifs_CDF = Transactions.objects.filter(membre=request.user.membre, devise="CDF", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0
    solde_objectifs_USD = Transactions.objects.filter(membre=request.user.membre, devise="USD", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0

    objectifs = Objectifs.objects.filter(membre=request.user.membre).order_by("-date_debut")

    for objectif in objectifs:
        objectif.pourcentage = float(objectif.montant / objectif.montant_cible ) * 100
        if timezone.now().date() > objectif.date_fin:
            objectif.statut = "Epuisé"
            objectif.save()

    context = {
        "objectifs": objectifs,
        "form": form,
        "solde_objectifs_CDF": solde_objectifs_CDF,
        "solde_objectifs_USD": solde_objectifs_USD
    }
    return render(request, "membres/objectifs.html", context)

@login_required
@require_POST
@csrf_exempt
def depot_objectif(request, objectif_id):
    try:
        data = json.loads(request.body)
        montant = data.get('montant')
        mot_de_passe = data.get('mot_de_passe')

        if not montant or not mot_de_passe:
            return JsonResponse({'error': 'Le montant et le mot de passe sont requis.'}, status=400)

        objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id, statut="En cours")

        if not check_password(mot_de_passe, request.user.password):
            return JsonResponse({'error': 'Mot de passe incorrect.'}, status=400)

        try:
            montant_depot = float(montant)
            if montant_depot <= 0 or montant_depot > (objectif.montant_cible - objectif.montant):
                return JsonResponse({'error': 'Montant de dépôt invalide.'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Montant de dépôt invalide.'}, status=400)

        # Vérification du solde du compte
        membre = request.user.membre
        compte = membre.compte_USD if objectif.devise == "USD" else membre.compte_CDF

        if compte.solde < montant_depot:
            return JsonResponse({'error': f'Solde insuffisant sur votre compte {objectif.devise}.'}, status=400)

        # Créer la transaction
        transaction = Transactions.objects.create(
            membre=membre,
            montant=montant_depot,
            devise=objectif.devise,
            type="depot_objectif",
            statut="Approuvé",
            date_approbation=timezone.now()
        )

        # Créer l'enregistrement de dépôt sur objectif
        DepotsObjectif.objects.create(
            objectif=objectif,
            transaction=transaction,
            montant=montant_depot,
            devise=objectif.devise,
            statut="Approuvé",
            date_approbation=timezone.now()
        )

        # Mettre à jour le montant de l'objectif
        objectif.montant += montant_depot
        if objectif.montant >= objectif.montant_cible:
            objectif.statut = "Atteint"
        objectif.save()

        # Retirer l'argent du compte principal
        compte.solde -= Decimal(str(montant_depot))
        compte.save()

        try:
            progress_percentage = float(objectif.montant / objectif.montant_cible) * 100
        except (TypeError, ZeroDivisionError):
            progress_percentage = 0
        progress_color = "green" if progress_percentage >= 100 else "orange" if progress_percentage > 50 else "red"

        return JsonResponse({
            'success': True,
            'message': 'Dépôt effectué avec succès !',
            'nouveau_montant_depose': objectif.montant,
            'montant_cible': objectif.montant_cible,
            'devise': objectif.devise,
            'nouveau_pourcentage': progress_percentage,
            'progress_color': progress_color,
            'objectif_slug': slugify(objectif.nom)
        })

    except Objectifs.DoesNotExist:
        return JsonResponse({'error': 'Objectif introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Vue pour retrait d'objectif
@login_required
@verifier_membre
def retrait_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id, statut="Atteint")
    membre = request.user.membre
    try:
        data = json.loads(request.body)
        password = data.get('password')

        if not check_password(password, request.user.password):
            return JsonResponse({'error': 'Mot de passe incorrect.'}, status=400)

        membre = request.user.membre
        compte = membre.compte_USD if objectif.devise == "USD" else membre.compte_CDF

        RetraitsObjectif.objects.create(
            membre=membre,
            objectif=objectif,
            montant=objectif.montant_cible,
            devise=objectif.devise,
            statut="Approuvé",
            transaction=Transactions.objects.create(
                membre=membre,
                montant=objectif.montant_cible,
                devise=objectif.devise,
                type="retrait_objectif",
                statut="Approuvé",
            )
        )

        #changement du statut de l'objectif
        objectif.statut = "Retiré"
        objectif.save()

        # Retirer l'argent du compte principal
        compte.solde += Decimal(str(objectif.montant_cible))
        compte.save()

        return JsonResponse({'success': True, 'message': f"Retrait de {objectif.montant_cible} {objectif.devise} pour l'objectif '{objectif.type}' effectué avec succès."})

    except Objectifs.DoesNotExist:
        return JsonResponse({'error': 'Objectif introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@verifier_membre
def annulation_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id, statut__in=['En cours', 'Epuisé'])
    membre = request.user.membre
    compte = membre.compte_USD if objectif.devise == "USD" else membre.compte_CDF

    try:
        data = json.loads(request.body)
        password = data.get('password')

        if not check_password(password, request.user.password):
            return JsonResponse({'success': False, 'error': 'Mot de passe incorrect.'}, status=400)

        AnnulationObjectif.objects.create(
            membre=membre,
            objectif=objectif,
            montant=objectif.montant,
            devise=objectif.devise,
            date_approbation=timezone.now(),
            statut="Approuvé",
            transaction=Transactions.objects.create(
                membre=membre,
                montant=objectif.montant,
                devise=objectif.devise,
                statut="Approuvé",
                type="annulation_objectif"
            )
        )

        # Retransférer l'argent qui était déjà affecté à l'objectif dans le compte principal
        compte.solde += Decimal(str(objectif.montant))
        compte.save()

        objectif.statut = "Annulé"
        objectif.montant = 0
        objectif.save()

        return JsonResponse({'success': True, 'message': f"Objectif '{objectif.nom}' annulé avec succès"})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': "Données JSON invalides"}, status=400)
    except Objectifs.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Objectif introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Vue pour la page de retrait du membre
@login_required
@verifier_membre
def retrait(request):
    membre = get_object_or_404(Membres, user=request.user)
    frais_retrais_benefice = 0.025

    #verfication s'il y a deja eu un retrait
    retraits = Retraits.objects.filter(membre=membre, statut="Approuvé")

    montant_benefices_cdf = benefices_actuelle(membre, "CDF")
    montant_benefices_usd = benefices_actuelle(membre, "USD")

    if request.method == "POST":
        form = TransactionsForm(request.POST)

        if form.is_valid():
            transaction = form.save(commit=False)

            montant_benefices = montant_benefices_cdf if transaction.devise == "CDF" else montant_benefices_usd
            montant_recu = float(transaction.montant) * (1 - frais_retrais_benefice),

            if transaction.montant > 0 and transaction.montant <= montant_benefices:                    
                Retraits.objects.create(
                    membre=membre,
                    montant=transaction.montant,
                    montant_recu = montant_recu,
                    frais=frais_retrais_benefice,
                    devise=transaction.devise,
                    transaction=Transactions.objects.create(
                        membre=membre,
                        montant=montant_recu,
                        devise=transaction.devise,
                        type="retrait"
                    )
                )

                # Crédit du compte
                compte = membre.compte_USD if transaction.devise == "USD" else membre.compte_CDF
                compte.solde += montant_recu
                compte.save()

                messages.success(request, "Votre demande de retrait a été effectue avec avec succès !")
                return redirect('membres:home')
            else:
                messages.error(request, "Montant insuffisant")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire")

    else:
        form = TransactionsForm()

    context = {
        "form": form,
        "retraits":retraits,
        "membre": membre,
        "montant_benefices_cdf": montant_benefices_cdf,
        "montant_benefices_usd": montant_benefices_usd,
        "date": timezone.now()
    }

    return render(request, "membres/retrait.html", context)

# Vue pour la page de gestion des transferts du membre
@login_required
@verifier_membre
def transfert(request):
    membre = get_object_or_404(Membres, user=request.user)

    if request.method == "POST":
        form = TransfertsForm(request.POST)
        if form.is_valid():
            montant = form.cleaned_data['montant']
            devise = form.cleaned_data['devise']
            numero_destinataire = form.cleaned_data['numero_destinataire']
            motif = form.cleaned_data['motif']

            # Vérification du mot de passe
            password = request.POST.get('password')
            if not check_password(password, request.user.password):
                messages.error(request, 'Mot de passe incorrect. Veuillez réessayer.')
                return render(request, "membres/transfert.html", {"form": form, "membre": membre})

            # Déterminer le destinataire (membre ou organisation)
            try:
                destinataire = Membres.objects.get(numero_telephone=numero_destinataire)
                destinataire_type = "membre"
            except Membres.DoesNotExist:
                try:
                    destinataire = Organisations.objects.get(numero_telephone=numero_destinataire)
                    destinataire_type = "organisation"
                except Organisations.DoesNotExist:
                    messages.error(request, "Numéro de destinataire invalide")
                    return render(request, "membres/transfert.html", {"form": form, "membre": membre})

            # Calcul du solde (à adapter en fonction de votre logique)
            solde_disponible = membre.solde_cdf if devise == "CDF" else membre.solde_usd

            if solde_disponible >= montant:
                try:
                    # Créer la transaction
                    transaction = Transactions.objects.create(
                        membre=membre,
                        montant=montant,
                        devise=devise,
                        description=f"Transfert vers {destinataire}",
                        operation="transfert",
                        operateur="membre",
                    )

                    # Créer le transfert
                    transfert = form.save(commit=False)
                    transfert.transaction = transaction
                    transfert.membre_expediteur = membre
                    transfert.expediteur = "membre"
                    transfert.destinataire = destinataire_type
                    transfert.motif = motif

                    if destinataire_type == "membre":
                        transfert.membre_destinataire = destinataire
                    else:
                        transfert.organisation_destinataire = destinataire

                    transfert.save()

                    # Mettre à jour le solde du membre (à adapter en fonction de votre logique)
                    if devise == "CDF":
                        membre.solde_cdf -= montant
                    else:
                        membre.solde_usd -= montant
                    membre.save()

                    messages.success(request, f"Transfert de {montant} {devise} effectué avec succès vers {destinataire}")
                    return redirect('membres:transfert')  # Redirigez vers une page appropriée

                except Exception as e:
                    messages.error(request, f"Une erreur s'est produite lors du transfert: {e}")
            else:
                messages.error(request, "Solde insuffisant")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire")
    else:
        form = TransfertsForm()

    return render(request, "membres/transfert.html", {"form": form, "membre": membre})

# Vue pour la page de gestion des transactions du membre
@login_required
@verifier_membre
def transactions(request):
    transactions = Transactions.objects.filter(membre=request.user.membre).order_by("-date")
    context = {
        "transactions": transactions,
    }
    
    return render(request, "membres/transactions.html", context)

@login_required
@verifier_membre
def transaction(request, transaction_id):
    transaction = get_object_or_404(Transactions, pk=transaction_id, membre=request.user.membre)
    context = {
        "transaction": transaction
    }
    return render(request, "membres/transaction.html", context)

# Vue pour la page de gestion des parametres du membre
@login_required
@verifier_membre
def parametres(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Votre mot de passe a été mis à jour avec succès")
            return redirect("membres:parametres")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "membres/parametres.html", {"form": form})

@login_required
@verifier_membre
def retirer_investissement(request):
    membre = request.user.membre
    solde_contribution_CDF = investissement_actuelle(membre,"CDF")
    solde_contribution_USD = investissement_actuelle(membre,"USD")

    Retraitcontrubution = RetraitContributions.objects.filter(transaction__membre=request.user.membre)
    frais = Decimal(0.1)
    
    if request.method == 'POST':
        form = TransactionsForm(request.POST)
        mot_de_passe = request.POST.get('mot_de_passe')

        if check_password(mot_de_passe, request.user.password):
            if form.is_valid():
                montant = form.cleaned_data['montant']
                devise = form.cleaned_data['devise']
                compte = membre.compte_USD if devise == "USD" else membre.compte_CDF
                solde_contribution = Transactions.objects.filter(membre=membre, devise=devise, statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

                if Prets.objects.filter(membre=membre, statut__in=["En attente","Approuvé", "Depassé"]).exists():
                    messages.error(request, "veiller d'abord payer le pret.")
                    return redirect("membres:contributions")

                if montant <= solde_contribution and montant > 0:
                    with db_transaction.atomic(): 

                        montant_admin = frais * Decimal(montant)
                        montant_membre = Decimal(montant) - montant_admin

                        RetraitContributions.objects.create(
                            membre=membre,
                            montant=montant,
                            frais=frais,
                            devise=devise,
                            statut="Approuvé",
                            transaction=Transactions.objects.create(
                                membre=membre,
                                montant=montant_membre,
                                devise=devise,
                                type="retrait investissement",
                                statut="Approuvé"
                            )
                        )

                        # Enregistrement du bénéfice pour l'administration (une seule fois)
                        BalanceAdmin.objects.create(
                            montant=montant_admin,
                            devise=devise,
                            type="Retrait investissement"
                        )

                        # Débit du compte
                        compte.solde += montant_membre
                        compte.save()

                        messages.success(request, "Investissement Retire avec succès.")
                        return redirect("membres:retirer_investissement")
                else:
                    messages.error(request, "Solde insuffisant ou montant invalide.")
            else:
                messages.error(request, "Formulaire invalide.")
        else:
            messages.error(request, "Mot de passe incorrect.")
    else:
        form = TransactionsForm()

    return render(request, "membres/retirer_contribution.html", {
        "form": form,
        "membre": membre,
        "Retraitcontrubution": Retraitcontrubution,
        "solde_contribution_CDF": solde_contribution_CDF,
        "solde_contribution_USD": solde_contribution_USD,
    })


# Vue pour la page de gestion des notifications du membre
@login_required
@verifier_membre
def notifications(request):
    return render(request, "membres/notifications.html")


# Traite le payement via mobile money chez un membre

@login_required
@verifier_membre
def recharger_compte(request):
    membre = request.user.membre
    frais_retrait = Decimal("0.035")

    if request.method == 'POST':
        form = SoldeForm(request.POST)
        mot_de_passe = request.POST.get("password")
        fournisseur = request.POST.get("fournisseur")
        if check_password(mot_de_passe, request.user.password):
            if form.is_valid():
                montant = form.cleaned_data['montant']
                devise = form.cleaned_data['devise']
                numero = form.cleaned_data['account_sender']
                net_montant = montant - (frais_retrait * montant)

                reference = f"TX-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                data = {
                    "numero": numero,
                    "montant": float(montant),
                    "devise": devise,
                    "reference": reference,
                    "fournisseur": fournisseur
                }

                if montant <= 0:
                    messages.error(request, "Montant invalide.")
                    return redirect("membres:home")

                # Appel à l'API de paiement
                if rechargerCompteService(data):
                    with db_transaction.atomic():
                        transaction = Transactions.objects.create(
                            membre=membre,
                            type="Rechargement compte",
                            montant=net_montant,
                            devise=devise,
                            statut="Approuvé",
                            date_approbation=timezone.now()
                        )

                        Solde.objects.create(
                            transaction=transaction,
                            montant=net_montant,
                            devise=devise,
                            account_sender=numero,
                            frais_retrait=frais_retrait
                        )

                        # Crédit du compte
                        compte = membre.compte_USD if devise == "USD" else membre.compte_CDF
                        compte.solde += net_montant
                        compte.save()

                        messages.success(request, "Rechargement effectué avec succès.")
                        return redirect("membres:home")
                else:
                    messages.error(request, "Échec du paiement. Veuillez réessayer.")
            else:
                messages.error(request, "Formulaire invalide.")
        else:
            messages.error(request, "Mot de passe incorrect.")
    else:
        form = SoldeForm()

    return render(request, "membres/home.html", {
        "form": form,
        "membre": membre,
    })

