from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Membres
from .forms import MembresForm, ModifierMembresForm
from agents.models import Agents, NumerosAgent
from administrateurs.models import Users, NumerosCompte, Villes, Communes, Quartiers, Avenues
from organisations.models import Organisations
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from transactions.models import Transactions, Prets, RemboursementsPret, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices, RetraitsObjectif, AnnulationObjectif
from transactions.forms import ContributionsForm, PretsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm, TypesPretForm, TransactionsForm, DepotsObjectifForm
from datetime import datetime, timedelta
from django.utils import timezone
from functools import wraps
from random import randint
from django.http import JsonResponse

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
    objectifs = Objectifs.objects.filter(membre=membre)

    solde_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    total_prets_CDF = Prets.objects.filter(transaction__membre=membre, devise="CDF", transaction__statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0
    total_prets_USD = Prets.objects.filter(transaction__membre=membre, devise="USD", transaction__statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0

    total_prets_rembourses_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0
    total_prets_rembourses_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="remboursement_pret").aggregate(total=Sum('montant'))['total'] or 0

    total_depot_objectif_CDF = Objectifs.objects.filter(membre=membre, devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Objectifs.objects.filter(membre=membre, devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_CDF = Retraits.objects.filter(membre=membre, devise="CDF", transaction__statut="Approuvé", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0
    total_retraits_USD = Retraits.objects.filter(membre=membre, devise="USD", transaction__statut="Approuvé", statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    benefices_CDF = Benefices.objects.filter(membre=membre, devise="CDF", statut=True).aggregate(total=Sum('montant'))['total'] or 0
    benefices_USD = Benefices.objects.filter(membre=membre, devise="USD", statut=True).aggregate(total=Sum('montant'))['total'] or 0

    transactions = Transactions.objects.filter(membre=membre).order_by("-date")

    context = {
        "membre": membre,
        "objectifs": objectifs,
        "total_prets_CDF": float(total_prets_CDF) - float(total_prets_rembourses_CDF),
        "total_prets_USD": float(total_prets_USD) - float(total_prets_rembourses_USD),
        "total_depot_objectif_CDF": total_depot_objectif_CDF,
        "total_depot_objectif_USD": total_depot_objectif_USD,
        "solde_CDF": solde_CDF,
        "solde_USD": solde_USD,
        "transactions": transactions,
        "benefices_CDF": float(benefices_CDF) - float(total_retraits_CDF),
        "benefices_USD": float(benefices_USD) - float(total_retraits_USD),
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
    solde_contribution_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_contribution_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    contributions = Contributions.objects.filter(transaction__membre=request.user.membre)
    contribution_actuelle = Contributions.objects.filter(transaction__membre=membre, mois=membre.mois_contribution, statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    context = {
        "membre": membre,
        "contribution_mensuelle": membre.contribution_mensuelle,
        "contribution_actuelle": contribution_actuelle,
        "montant_restant": float(membre.contribution_mensuelle.montant) - contribution_actuelle,
        "contributions": contributions,
        "solde_contribution_CDF": solde_contribution_CDF,
        "solde_contribution_USD": solde_contribution_USD
    }
    return render(request, "membres/contributions.html", context)

@login_required
@verifier_membre
def contribuer(request):
    membre = request.user.membre
    contribution_actuelle = Contributions.objects.filter(transaction__membre=membre, mois=membre.mois_contribution, statut="Approuvé").aggregate(total=Sum('montant'))['total'] or 0

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == 'POST':
        form = TransactionsForm(request.POST, request.FILES)
        mot_de_passe = request.POST.get('mot_de_passe')

        if check_password(mot_de_passe, request.user.password):
            if form.is_valid():
                contribution_mensuelle = membre.contribution_mensuelle
                transaction = form.save(commit=False)

                transaction.devise = contribution_mensuelle.devise
                transaction.agent = transaction.numero_agent.agent
                transaction.type = "contribution"
                transaction.statut = "En attente"
                transaction.membre = membre

                if not Transactions.objects.filter(membre=membre, type="contribution", statut="En attente").exists():
                    if transaction.montant > 0 and transaction.montant <= float(contribution_mensuelle.montant) - contribution_actuelle:
                        transaction.save()

                        Contributions.objects.create(
                                transaction=transaction,
                                montant=transaction.montant,
                                devise=transaction.devise,
                                mois=membre.mois_contribution
                            )

                        messages.success(request, "Votre contribution a été enregistrée avec succès !")
                        return redirect('membres:contributions')
                    
                    else:
                        messages.error(request, "Le montant doit être supérieur à zéro et inférieur ou égal au montant de votre contribution mensuelle")
                else:
                    messages.error(request, "Vous avez déjà une contribution en attente")

            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")

        else:
            messages.error(request, "Mot de passe incorrect")

    else:
        form = TransactionsForm()

    context = {
        "form": form,
        "membre": membre,
        "numeros_categories": numeros_categories,
        "contribution_mensuelle": membre.contribution_mensuelle,
        "contribution_actuelle": contribution_actuelle,
        "montant_restant": float(membre.contribution_mensuelle.montant) - contribution_actuelle
    }

    return render(request, "membres/contribuer.html", context)

# Vue pour la page de demande de pret du membre
@login_required
@verifier_membre
def demande_pret(request):
    types_pret = TypesPret.objects.all() # Récupérer tous les types de pret
    demandes_pret = Prets.objects.filter(membre=request.user.membre)

    # Solde contribution
    solde_contribution_CDF = Transactions.objects.filter(membre=request.user.membre, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_contribution_USD = Transactions.objects.filter(membre=request.user.membre, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    # Convert USD to CDF for consistent comparison (using an exchange rate, adjust as needed)
    taux_de_change = 2800
    solde_total_contribution = (solde_contribution_CDF + (solde_contribution_USD * taux_de_change)) * 3
    solde_max = (float(Transactions.objects.filter(devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0) +
                float(Transactions.objects.filter(devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0) * taux_de_change +
                float(Transactions.objects.filter(devise="CDF", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0) +
                float(Transactions.objects.filter(devise="USD", statut="Approuvé", type="depot_inscription").aggregate(total=Sum('montant'))['total'] or 0) * taux_de_change -
                (float(Transactions.objects.filter(devise="CDF", statut="Approuvé", type="pret").aggregate(total=Sum('montant'))['total'] or 0) +
                float(Transactions.objects.filter(devise="USD", statut="Approuvé", type="pret").aggregate(total=Sum('montant'))['total'] or 0) * taux_de_change +
                float(Transactions.objects.filter(devise="CDF", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0) +
                float(Transactions.objects.filter(devise="USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0) * taux_de_change)) * 2/3

    solde_total_contribution = solde_total_contribution * 3 if solde_total_contribution < solde_max else solde_max

    if request.method == "POST":
        form = PretsForm(request.POST)

        if form.is_valid():
            # Vérification du mot de passe
            mot_de_passe = request.POST.get('password')

            if check_password(mot_de_passe, request.user.password):
                pret = form.save(commit=False)  # Créer l'objet pret sans l'enregistrer
                pret.membre = request.user.membre

                pret.montant_remboursé = pret.montant
                pret.montant = float(pret.montant_remboursé) - (float(pret.montant) * 0.10) #(pret.montant * (pret.type_pret.taux_interet / 100))

                pret.date_remboursement = datetime.now() + timedelta(days=120) #timedelta(days=pret.type_pret.delai_remboursement)  # Définir la date de remboursement
                
                if not Transactions.objects.filter(membre=request.user.membre, type="retrait_tout", statut__in=["En attente", "Demande"]).exists():
                    if not Prets.objects.filter(membre=request.user.membre, statut="En attente").exists():
                        if not Prets.objects.filter(membre=request.user.membre, transaction__statut__in=["Demande", "En attente"], statut__in=["En attente", "Approuvé"]).exists():
                            if pret.montant_remboursé > 0 and pret.montant_remboursé * (2800 if pret.devise == "USD" else 1) <= solde_total_contribution:
                                
                                pret.transaction = Transactions.objects.create(
                                    membre=request.user.membre,
                                    montant=pret.montant,
                                    devise=pret.devise,
                                    type="pret",
                                )

                                pret.save()  # Enregistrer l'objet pret
                                messages.success(request, 'Votre demande de pret a été soumise avec succès !')
                                return redirect('membres:demande_pret')
                            else:
                                # Solde insuffisant ou prets en cours, afficher un message d'erreur
                                messages.error(request, f'Montant max dépassé')
                        else:
                            messages.error(request, 'Vous avez déjà un pret approuvé, veuillez le rembourser')
                    else:
                        messages.error(request, 'Vous avez déjà une demande de pret en cours, veuillez patienter qu\'elle soit traitée')

                else:
                    messages.error(request, "Vous avez déjà une demande de retrait totale en attente")

            else:
                # Mot de passe incorrect, afficher un message d'erreur
                messages.error(request, 'Mot de passe incorrect. Veuillez réessayer.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')

    else:
        form = PretsForm()

    context = {
        "form": form,
        "types_pret": types_pret,
        "demandes_pret": demandes_pret,
        "taux_change": taux_de_change,
        "solde_total_contribution_cdf": solde_total_contribution,
        "solde_total_contribution_usd": solde_total_contribution / taux_de_change
    }

    return render(request, "membres/demande_pret.html", context)

# Vue pour la page de demande de pret du membre
@login_required
@verifier_membre
def rembourser_pret(request, transaction_id):
    pret = get_object_or_404(Prets, transaction=get_object_or_404(Transactions, pk=transaction_id, membre=request.user.membre, type="pret", statut="Approuvé"), statut="Approuvé")

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}

    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        form = TransactionsForm(request.POST, request.FILES)
    
        if form.is_valid():
            # Vérification du mot de passe
            mot_de_passe = request.POST.get('password')

            if check_password(mot_de_passe, request.user.password):
                transaction = form.save(commit=False)
                transaction.membre=request.user.membre
                transaction.agent=transaction.numero_agent.agent
                transaction.type= "remboursement_pret"
                transaction.statut="En attente"
                transaction.description = f"Remboursement de pret N°{pret.pk}"

                if not Transactions.objects.filter(membre=request.user.membre, statut="En attente", type="remboursement_pret").exists():
                    if transaction.montant > 0 and transaction.montant <= (pret.montant_remboursé - pret.solde_remboursé):
                        transaction.save()

                        RemboursementsPret.objects.create(
                            pret=pret,
                            montant=transaction.montant,
                            devise=transaction.devise,
                            transaction=transaction
                        )

                        messages.success(request, 'Votre demande de pret a été soumise avec succès !')
                        return redirect('membres:demande_pret')  # Redirigez vers
                
                    else:
                        # Solde insuffisant ou prets en cours, afficher un message d'erreur
                        messages.error(request, 'Solde invalide, veuillez réessayer')
                
                else:
                    messages.error(request, 'Vous avez déjà une demande de remboursement en cours, veuillez patienter qu\'elle soit traitée')

            else:
                # Mot de passe incorrect, afficher un message d'erreur
                messages.error(request, 'Mot de passe incorrect. Veuillez réessayer')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire')

    else:
        form = TransactionsForm(request.POST)
        
    context = {
        "form": form,
        "pret": pret,
        "montant_restant": pret.montant_remboursé - pret.solde_remboursé,
        "numeros_categories": numeros_categories
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

            if not Objectifs.objects.filter(membre=request.user.membre, nom=objectif.nom).exists():
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

    context = {
        "objectifs": objectifs,
        "form": form,
        "solde_objectifs_CDF": solde_objectifs_CDF,
        "solde_objectifs_USD": solde_objectifs_USD
    }
    return render(request, "membres/objectifs.html", context)

# Vue pour la page de dépôt sur objectif du membre
@login_required
@verifier_membre
def depot_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id, statut="En cours")

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        depot_objectif_form = DepotsObjectifForm(request.POST)
        form = TransactionsForm(request.POST, request.FILES)
        mot_de_passe = request.POST.get('mot_de_passe')
        
        if check_password(mot_de_passe, request.user.password):
            if form.is_valid() and depot_objectif_form.is_valid():
                try:
                    depot_objectif = depot_objectif_form.save(commit=False)
                    depot_objectif.objectif = objectif

                    transaction = form.save(commit=False)

                    transaction.membre = request.user.membre
                    transaction.devise = depot_objectif.devise = depot_objectif.objectif.devise
                    transaction.agent = transaction.numero_agent.agent

                    transaction.type = "depot_objectif"
                    transaction.statut = "En attente"

                    if not Transactions.objects.filter(membre=request.user.membre, type="depot_objectif", statut="En attente").exists():
                        if transaction.montant > 0 and transaction.montant <= float(objectif.montant_cible) - float(objectif.montant):
                            transaction.save()

                            depot_objectif.transaction = transaction
                            depot_objectif.save()

                            messages.success(request, "Votre dépôt sur objectif a été soumis avec succès !")
                            return redirect('membres:depot_objectif', objectif_id=objectif_id, permanent=True)
                        else:
                            messages.error(request, "Le montant doit être supérieur à zéro et inférieur ou égal au montant cible de l'objectif")
                    
                    else:
                        messages.error(request, "Vous avez déjà un dépôt en attente pour cet objectif")

                except Agents.DoesNotExist:
                    messages.error(request, "Numéro d'agent invalide")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire")

        else:
            messages.error(request, "Mot de passe incorrect")

    else:
        form = TransactionsForm()
        depot_objectif_form = DepotsObjectifForm(initial={"objectif": objectif_id, "devise": objectif.devise})

    context = {
        "form": form,
        "depot_objectif_form": depot_objectif_form,
        "numeros_categories": numeros_categories,
        "objectif": objectif,
        "montant_restant": objectif.montant_cible - objectif.montant
    }

    return render(request, "membres/depot_objectif.html", context)

# Vue pour retrait d'objectif
@login_required
@verifier_membre
def retrait_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id, statut='Atteint')
    membre = request.user.membre

    if request.method == 'POST':
        password = request.POST.get('password')

        if check_password(password, request.user.password):
            if not Transactions.objects.filter(membre=membre, type="retrait_tout", statut__in=["En attente", "Demande"]).exists():
                if not RetraitsObjectif.objects.filter(membre=membre, transaction__statut__in=["Demande", "En attente"], statut__in=["En attente", "Approuvé"]).exists():
                    montant_total_USD = objectif.montant_cible / 2800 if objectif.devise == "CDF" else objectif.montant_cible
    
                    if montant_total_USD > 0 and montant_total_USD <= 10: frais = 0.085
                    elif montant_total_USD > 10 and montant_total_USD <= 20: frais = 0.058
                    elif montant_total_USD > 20 and montant_total_USD <= 50: frais = 0.0295
                    elif montant_total_USD > 50 and montant_total_USD <= 400: frais = 0.0175
                    elif montant_total_USD > 400: frais = 0.01

                    frais = 0

                    RetraitsObjectif.objects.create(
                        membre=membre,
                        objectif=objectif,
                        montant=objectif.montant_cible,
                        devise=objectif.devise,
                        frais=frais,
                        transaction=Transactions.objects.create(
                            membre=membre,
                            montant=objectif.montant_cible * (1 - frais),
                            devise=objectif.devise,
                            type="retrait_objectif"
                        )
                    )

                    messages.success(request, f"Retrait de {objectif.montant_cible} {objectif.devise} pour l'objectif '{objectif.nom}' envoyé avec succès")

                else:
                    messages.error(request, "Vous avez une demande de retrait en attente, patientez svp !")

            else:
                messages.error(request, "Vous avez déjà une demande de retrait totale en attente")

        else:
            messages.error(request, "Mot de passe incorrect")

    return redirect('membres:objectifs')

# Vue pour retrait d'objectif
@login_required
@verifier_membre
def annulation_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id, statut__in=['En cours', 'Epuisé'])
    membre = request.user.membre

    if request.method == 'POST':
        password = request.POST.get('password')

        if check_password(password, request.user.password):
            if not Transactions.objects.filter(membre=membre, type="retrait_tout", statut__in=["En attente", "Demande"]).exists():
                if not Transactions.objects.filter(membre=membre, type="annulation_objectif", statut="Demande").exists():
                    montant_total_USD = objectif.montant / 2800 if objectif.devise == "CDF" else objectif.montant
    
                    if montant_total_USD > 0 and montant_total_USD <= 10: frais = 0.085
                    elif montant_total_USD > 10 and montant_total_USD <= 20: frais = 0.058
                    elif montant_total_USD > 20 and montant_total_USD <= 50: frais = 0.0295
                    elif montant_total_USD > 50 and montant_total_USD <= 400: frais = 0.0175
                    elif montant_total_USD > 400: frais = 0.01

                    AnnulationObjectif.objects.create(
                        membre=membre,
                        objectif=objectif,
                        montant=objectif.montant,
                        devise=objectif.devise,
                        frais=frais,
                        transaction=Transactions.objects.create(
                            membre=membre,
                            montant=objectif.montant * (1 - frais),
                            devise=objectif.devise,
                            type="annulation_objectif"
                        )
                    )

                    messages.success(request, f"Annulation de l'objectif '{objectif.nom}' envoyé avec succès")

                else:
                    messages.error(request, "Vous avez une demande d'annulation en attente, patientez svp !")

            else:
                messages.error(request, "Vous avez déjà une demande de retrait totale en attente")

        else:
            messages.error(request, "Mot de passe incorrect")

    return redirect('membres:objectifs')

# Vue pour voir un objectif en details
@login_required
@verifier_membre
def objectif(request, objectif_id):
    objectif = Objectifs.objects.get(pk=objectif_id)
    return render(request, "membres/objectif_details.html", {"objectif": objectif})

# Vue pour la page de retrait du membre
@login_required
@verifier_membre
def retrait(request):
    membre = get_object_or_404(Membres, user=request.user)
    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()

    montant_retraits = float(Transactions.objects.filter(membre=membre, devise="CDF" if membre.contribution_mensuelle.devise == "CDF" else "USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0)
    montant_benefices = float(Benefices.objects.filter(membre=membre, devise="CDF" if membre.contribution_mensuelle.devise == "CDF" else "USD", statut=True).aggregate(total=Sum('montant'))['total'] or 0) - montant_retraits

    if request.method == "POST":
        form = TransactionsForm(request.POST)
        if timezone.now().month == 12:

            if form.is_valid():
                transaction = form.save(commit=False)

                if not Transactions.objects.filter(membre=membre, type="retrait_tout", statut__in=["En attente", "Demande"]).exists():
                    if not Retraits.objects.filter(membre=membre, transaction__statut__in=["Demande", "En attente"], statut__in=["En attente", "Approuvé"]).exists():
                        if transaction.montant > 0 and transaction.montant <= montant_benefices:
                            montant = transaction.montant if membre.contribution_mensuelle.devise == "USD" else transaction.montant / 2800

                            # montant selon les frais de retrait
                            if montant > 0 and montant <= 10: frais = 0.085
                            elif montant > 10 and montant <= 20: frais = 0.058
                            elif montant > 20 and montant <= 50: frais = 0.0295
                            elif montant > 50 and montant <= 400: frais = 0.0175
                            elif montant > 400: frais = 0.01
                            
                            Retraits.objects.create(
                                membre=membre,
                                montant=transaction.montant,
                                frais=frais,
                                devise=transaction.devise,
                                transaction=Transactions.objects.create(
                                    membre=membre,
                                    montant=float(transaction.montant) * (1 - frais),
                                    devise=transaction.devise,
                                    type="retrait"
                                )
                            )

                            messages.success(request, "Votre demande de retrait a été soumise avec succès !")
                            return redirect('membres:home')
                        else:
                            messages.error(request, "Montant insuffisant")
                    else:
                        messages.error(request, "Vous avez déjà une demande de retrait en attente")

                else:
                    messages.error(request, "Vous avez déjà une demande de retrait totale en attente")
            
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire")
        
        else:
            messages.error(request, "Les retraits ne sont possibles qu'en Décembre")
    else:
        form = TransactionsForm()

    context = {
        "form": form,
        "membre": membre,
        "montant_benefices": montant_benefices,
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
def retirer_tout(request):
    membre = request.user.membre
    
    montant_contributions = float(Transactions.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, type="contribution", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0)
    montant_objectifs = (float(Objectifs.objects.filter(membre=membre, devise="CDF", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(Sum('montant'))['montant__sum'] or 0) + float(Objectifs.objects.filter(membre=membre, devise="USD", statut__in=["En cours", "Atteint", "Epuisé"]).aggregate(Sum('montant'))['montant__sum'] or 0) * 2800) * (1/2800 if membre.contribution_mensuelle.devise == "USD" else 1)
    montant_benefices = float(Benefices.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, statut=True).aggregate(Sum('montant'))['montant__sum'] or 0) - float(Retraits.objects.filter(membre=membre, devise=membre.contribution_mensuelle.devise, statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0)

    montant_total = montant_contributions + montant_objectifs + montant_benefices

    if request.method == "POST":
        mot_de_passe = request.POST.get('mot_de_passe')
        
        if check_password(mot_de_passe, request.user.password):
            if not Transactions.objects.filter(membre=membre, type="retrait_tout", statut__in=["En attente", "Demande"]).exists():
                if not Prets.objects.filter(membre=request.user.membre, statut="Approuvé").exists():
                    if montant_total > 0:
                        Transactions.objects.create(
                            membre=membre,
                            montant=montant_total,
                            devise=membre.contribution_mensuelle.devise,
                            description=f"Retrait total du solde",
                            type="retrait_tout"
                        )
                        messages.success(request, "Votre demande de retrait a été soumise avec succès ! Veuillez attendre l'approbation de l'administrateur")
                    else:
                        messages.error(request, "Vous n'avez pas de solde à retirer")
                else:
                    messages.error(request, "Vous devez rembourser vos prêts avant de pouvoir retirer votre solde")
            
            else:
                messages.error(request, "Vous avez déjà une demande de retrait totale en attente")
        else:
            messages.error(request, "Mot de passe incorrect")
    
    return redirect('membres:contributions')

# Vue pour la page de gestion des notifications du membre
@login_required
@verifier_membre
def notifications(request):
    return render(request, "membres/notifications.html")
