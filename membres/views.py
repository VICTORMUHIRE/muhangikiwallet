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
from .forms import MembresForm
from agents.models import Agents, NumerosAgent
from administrateurs.models import Users, NumerosCompte
from organisations.models import Organisations
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from transactions.models import Transactions, Prêts, TypesPrêt, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices
from transactions.forms import ContributionsForm, PrêtsForm, TransfertsForm, RetraitsForm, DepotsInscriptionForm, TypesPrêtForm, TransactionsForm, DepotsObjectifForm
from datetime import datetime, timedelta
from django.utils import timezone
from functools import wraps
from random import randint

def verifier_membre(func):
    def verify(request, *args, **kwargs):
        if request.user.is_membre():
            if request.user.membre.status and Transactions.objects.filter(membre=request.user.membre, type="depot_inscription").first().statut == "Approuvé":
                return func(request, *args, **kwargs)
            else : return redirect("membres:statut")

        else: return redirect("index")

    return wraps(func)(verify)

# Vue pour la page de statut des membres
@login_required
def statut(request):
    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == 'POST':
        form = TransactionsForm(request.POST, request.FILES, instance=Transactions.objects.filter(membre=request.user.membre, type="depot_inscription").first())
        mot_de_passe = request.POST.get('mot_de_passe')

        if check_password(mot_de_passe, request.user.password):
            if form.is_valid():
                try:
                    transaction = form.save(commit=False)

                    depot_inscription = DepotsInscription.objects.filter(transaction=transaction).first()
                    depot_inscription.devise = transaction.devise

                    depot_inscription.date = timezone.now()
                    transaction.statut = depot_inscription.statut = "En attente"

                    transaction.montant = depot_inscription.montant
                    transaction.agent = transaction.numero_agent.agent
                    depot_inscription.date = transaction.date = timezone.now()
                    
                    transaction.save()
                    depot_inscription.save()

                    messages.success(request, "Votre dépot d'inscription a été soumise avec succès !")
                    return redirect('membres:home')

                except Agents.DoesNotExist:
                    messages.error(request, "Numéro d'agent invalide.")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")

        else:
            messages.error(request, "Mot de passe incorrect.")

    else:
        form = TransactionsForm(instance=Transactions.objects.filter(membre=request.user.membre, type="depot_inscription").first())
    
    membre_form = MembresForm(instance=request.user.membre)
    return render(request, 'membres/statut.html', {'reseaux': reseaux, 'numeros_categories': numeros_categories, 'form': form, 'membre_form': membre_form}) # Pass the form to the template

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

            DepotsInscription.objects.create(
                transaction=Transactions.objects.create(
                    membre=membre,
                    montant=10,
                    devise="USD",
                    type="depot_inscription"
                )
            )
            login(request, membre.user)
            return redirect("login")
        
    else: form = MembresForm()
    
    return render(request, "membres/inscription.html", {"form": form})

# Vue pour la page de changement de mot de passe des membres
def password_reset(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
            return redirect("muhangiki_wallet:login")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
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

    total_prêts_CDF = Prêts.objects.filter(transaction__membre=membre, devise="CDF", statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0
    total_prêts_USD = Prêts.objects.filter(transaction__membre=membre, devise="USD", statut="Approuvé").aggregate(total=Sum('montant_remboursé'))['total'] or 0

    total_depot_objectif_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0
    total_depot_objectif_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="depot_objectif").aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_CDF = Transactions.objects.filter(membre=membre, devise="CDF", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0
    total_retraits_USD = Transactions.objects.filter(membre=membre, devise="USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0

    benefices_CDF = Benefices.objects.filter(membre=membre, devise="CDF", statut=True).aggregate(total=Sum('montant'))['total'] or 0
    benefices_USD = Benefices.objects.filter(membre=membre, devise="USD", statut=True).aggregate(total=Sum('montant'))['total'] or 0

    transactions = Transactions.objects.filter(membre=membre).order_by("-date")

    context = {
        "membre": membre,
        "objectifs": objectifs,
        "total_prêts_CDF": total_prêts_CDF,
        "total_prêts_USD": total_prêts_USD,
        "total_depot_objectif_CDF": total_depot_objectif_CDF,
        "total_depot_objectif_USD": total_depot_objectif_USD,
        "solde_CDF": solde_CDF,
        "solde_USD": solde_USD,
        "transactions": transactions,
        "benefices_CDF": benefices_CDF - total_retraits_CDF,
        "benefices_USD": benefices_USD - total_retraits_USD,
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
            filename = fs.save("photos_passport/" + photo_file.name, photo_file)
            uploaded_file_url = fs.url(filename)

            membre = request.user.membre

            if fs.exists(str(settings.BASE_DIR) + membre.photo_passport.name):
                fs.delete(str(settings.BASE_DIR) + membre.photo_passport.name)

            membre.photo_passport = uploaded_file_url  # Update the photo_passport field
            membre.save()

            messages.success(request, 'Photo de profil mise à jour avec succès.')
            return redirect('membres:profile')
    else:
        form = MembresForm(instance=membre)

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

    contributions = Transactions.objects.filter(membre=request.user.membre, type="contribution")
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
                try:
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

                            contribution = Contributions.objects.create(
                                transaction=transaction,
                                montant=transaction.montant,
                                devise=transaction.devise,
                                mois=transaction.membre.mois_contribution
                            )

                            messages.success(request, "Votre contribution a été enregistrée avec succès !")
                            return redirect('membres:contributions')
                        else:
                            messages.error(request, "Le montant doit être supérieur à zéro et inférieur ou égal au montant de votre contribution mensuelle")
                    else:
                        messages.error(request, "Vous avez déjà une contribution en attente.")

                except Agents.DoesNotExist:
                    messages.error(request, "Numéro d'agent invalide.")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")

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

# Vue pour la page de demande de prêt du membre
@login_required
@verifier_membre
def demande_prêt(request):
    types_prêt = TypesPrêt.objects.all() # Récupérer tous les types de prêt
    demandes_prêt = Transactions.objects.filter(membre=request.user.membre, type="prêt")

    # Solde contribution
    solde_contribution_CDF = Transactions.objects.filter(membre=request.user.membre, devise="CDF", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0
    solde_contribution_USD = Transactions.objects.filter(membre=request.user.membre, devise="USD", statut="Approuvé", type="contribution").aggregate(total=Sum('montant'))['total'] or 0

    # Convert USD to CDF for consistent comparison (using an exchange rate, adjust as needed)
    taux_de_change = 2800
    solde_total_contribution = solde_contribution_CDF + (solde_contribution_USD * taux_de_change)

    reseaux = NumerosAgent.objects.values_list('reseau', flat=True).distinct()
    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        form = PrêtsForm(request.POST)
        transaction_form = TransactionsForm(request.POST)

        if form.is_valid() and transaction_form.is_valid():
            # Vérification du mot de passe
            mot_de_passe = request.POST.get('password')

            if check_password(mot_de_passe, request.user.password):
                prêt = form.save(commit=False)  # Créer l'objet prêt sans l'enregistrer
                transaction = transaction_form.save(commit=False)
                transaction.membre = request.user.membre
                transaction.agent = transaction.numero_agent.agent
                transaction.type = "prêt"
                transaction.statut = "Initialisation"

                prêt.montant_remboursé = prêt.montant
                transaction.montant = prêt.montant = float(prêt.montant_remboursé) - (float(prêt.montant) * 0.10) #(prêt.montant * (prêt.type_prêt.taux_interet / 100))

                prêt.date_remboursement = datetime.now() + timedelta(days=120) #timedelta(days=prêt.type_prêt.delai_remboursement)  # Définir la date de remboursement

                if not Prêts.objects.filter(transaction__membre=request.user.membre, statut="En attente").exists():
                    if not Prêts.objects.filter(transaction__membre=request.user.membre, statut="Approuvé").exists():
                        if prêt.montant_remboursé > 0 and prêt.montant_remboursé * (2800 if prêt.devise == "USD" else 1) <= 3*solde_total_contribution:
                            # Solde suffisant, enregistrer la transaction et le prêt
                            transaction.save()
                            prêt.transaction = transaction
                            prêt.save()  # Enregistrer l'objet prêt
                            messages.success(request, 'Votre demande de prêt a été soumise avec succès !')
                            return redirect('membres:demande_prêt')  # Redirigez vers
                        else:
                            # Solde insuffisant ou prêts en cours, afficher un message d'erreur
                            messages.error(request, f'Vous ne pouvez demander plus de 3x votre contribution actuelle')
                    else:
                        messages.error(request, 'Vous avez déjà un prêt approuvé, veuillez le rembourser')
                else:
                    messages.error(request, 'Vous avez déjà une demande de prêt en cours, veuillez patienter qu\'elle soit traitée')
            
            else:
                # Mot de passe incorrect, afficher un message d'erreur
                messages.error(request, 'Mot de passe incorrect. Veuillez réessayer.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')

    else:
        form = PrêtsForm()
        transaction_form = TransactionsForm(request.POST)

    context = {
        "form": form,
        "transaction_form": transaction_form,
        "types_prêt": types_prêt,
        "demandes_prêt": demandes_prêt,
        "numeros_categories": numeros_categories,
        "taux_change": taux_de_change,
        "solde_total_contribution_cdf": solde_total_contribution * 3,
        "solde_total_contribution_usd": solde_total_contribution * 3 / taux_de_change
    }

    return render(request, "membres/demande_prêt.html", context)

# Vue pour la page de demande de prêt du membre
@login_required
@verifier_membre
def rembourser_prêt(request, transaction_id):
    prêt = Prêts.objects.get(transaction=get_object_or_404(Transactions, pk=transaction_id, membre=request.user.membre, type="prêt"))
    if prêt.statut == "Remboursé":  return redirect("membres:demande_prêt")

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
                transaction.type= "remboursement_prêt"
                transaction.statut="En attente"

                if not Transactions.objects.filter(membre=request.user.membre, statut="En attente", type="remboursement_prêt").exists():
                    if transaction.montant > 0 and transaction.montant <= (prêt.montant_remboursé - prêt.solde_remboursé):
                        # Solde suffisant, enregistrer la transaction et le prêt
                        transaction.save()
                        messages.success(request, 'Votre demande de prêt a été soumise avec succès !')
                        return redirect('membres:demande_prêt')  # Redirigez vers
                
                    else:
                        # Solde insuffisant ou prêts en cours, afficher un message d'erreur
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
        "prêt": prêt,
        "montant_restant": prêt.montant_remboursé - prêt.solde_remboursé,
        "numeros_categories": numeros_categories
    }

    return render(request, "membres/rembourser_prêt.html", context)

# Vue pour la page de gestion des objectifs du membre
@login_required
@verifier_membre
def objectifs(request):
    if request.method == "POST":
        form = ObjectifsForm(request.POST)
        if form.is_valid():
            form.instance.membre = request.user.membre
            form.save()
            messages.success(request, "Votre objectif a été créé avec succès.")
        else: messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

        return redirect("membres:objectifs")
    
    else: form = ObjectifsForm()
    
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
def dépot_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id)

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
                            return redirect('membres:dépot_objectif', objectif_id=objectif_id, permanent=True)
                        else:
                            messages.error(request, "Le montant doit être supérieur à zéro et inférieur ou égal au montant cible de l'objectif.")
                    else:
                        messages.error(request, "Vous avez déjà un dépôt en attente pour cet objectif.")

                except Agents.DoesNotExist:
                    messages.error(request, "Numéro d'agent invalide.")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")

        else:
            messages.error(request, "Mot de passe incorrect.")

    else:
        form = TransactionsForm()
        depot_objectif_form = DepotsObjectifForm(initial={"objectif": objectif_id, "devise": objectif.devise})

    context = {
        "form": form,
        "depot_objectif_form": depot_objectif_form,
        "numeros_categories": numeros_categories,
        "objectif": objectif
    }

    return render(request, "membres/depot_objectif.html", context)

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

    montant_retraits = Transactions.objects.filter(membre=membre, devise="CDF" if membre.contribution_mensuelle.devise == "CDF" else "USD", statut="Approuvé", type="retrait").aggregate(total=Sum('montant'))['total'] or 0
    montant_benefices = Benefices.objects.filter(membre=membre, devise="CDF" if membre.contribution_mensuelle.devise == "CDF" else "USD", statut=True).aggregate(total=Sum('montant'))['total'] or 0 - montant_retraits

    numeros_categories = {reseau: [] for reseau in reseaux}
    for reseau in reseaux:
        for numero_agent in NumerosAgent.objects.filter(reseau=reseau):
            numeros_categories[reseau].append((numero_agent.numero, numero_agent.pk))

    if request.method == "POST":
        form = TransactionsForm(request.POST)
        if timezone.now().month == 12:

            if form.is_valid():
                transaction = form.save(commit=False)

                if transaction.montant > 0 and transaction.montant <= montant_benefices:
                    transaction.membre = membre
                    transaction.agent = transaction.numero_agent.agent
                    transaction.type = "retrait"
                    transaction.statut = "En attente"
                    transaction.save()

                    retrait = Retraits.objects.create(
                        transaction=transaction,
                        montant=transaction.montant,
                        devise=transaction.devise
                    )

                    messages.success(request, "Votre demande de retrait a été soumise avec succès !")
                    return redirect('membres:home')
                
                else:
                    messages.error(request, "Montant insuffisant")

            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        else:
            messages.error(request, "Les retraits ne sont possibles qu'en Décembre")
    else:
        form = TransactionsForm()

    context = {
        "form": form,
        "membre": membre,
        "numeros_categories": numeros_categories,
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
                    messages.error(request, "Numéro de destinataire invalide.")
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

                    messages.success(request, f"Transfert de {montant} {devise} effectué avec succès vers {destinataire}.")
                    return redirect('membres:transfert')  # Redirigez vers une page appropriée

                except Exception as e:
                    messages.error(request, f"Une erreur s'est produite lors du transfert: {e}")
            else:
                messages.error(request, "Solde insuffisant.")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
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

# Vue pour la page de gestion des paramètres du membre
@login_required
@verifier_membre
def paramètres(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Votre mot de passe a été mis à jour avec succès.")
            return redirect("membres:paramètres")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "membres/paramètres.html", {"form": form})

# Vue pour la page de gestion des notifications du membre
@login_required
@verifier_membre
def notifications(request):
    return render(request, "membres/notifications.html")
