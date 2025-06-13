from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned 
import traceback
from decimal import Decimal,InvalidOperation
import json
from django.db.models import Q
from django.db import transaction 
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
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from membres.service import benefices_actuelle, investissement_actuelle, rechargerCompteService
from membres.tasks import partager_benefices
from .models import Membres
from .forms import MembresForm, ModifierMembresForm
from administrateurs.models import Users, NumerosCompte,Villes, Communes, Quartiers, Avenues
from objectifs.models import Objectifs
from objectifs.forms import ObjectifsForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from transactions.models import BalanceAdmin, RetraitContributions, Solde, Transactions, Prets, RemboursementsPret, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices, RetraitsObjectif, AnnulationObjectif
from transactions.forms import  PretsForm, SoldeForm, TransfertsForm,TransactionsForm, DepotsObjectifForm
from datetime import datetime, timedelta
from django.utils import timezone
from functools import wraps
from random import randint
from django.http import JsonResponse
from django.db import transaction as db_transaction

def verifier_membre(func):
    def verify(request, *args, **kwargs):
        if request.user.is_membre():
            if request.user.membre.status:
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
# Vue pour la page de statut des membres
@login_required
def statut(request):
    depot_inscription = DepotsInscription.objects.filter(membre=request.user.membre).first()

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
        "depot_inscription": depot_inscription
    }

    return render(request, 'membres/statut.html', context) 


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
    }

    return render(request, "membres/home.html", context)

@login_required
@verifier_membre
def balance(request):
    membre = request.user.membre
    balance_cdf = membre.compte_CDF.solde
    balance_usd = membre.compte_USD.solde

    form = SoldeForm()

    context = {
        "membre": membre,
        "balance_cdf": balance_cdf,
        "balance_usd": balance_usd,
        "form":form
    }
    return render(request, "membres/balance.html",context)

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
                if Transactions.objects.filter(membre=membre, type="retrait_investissement", statut__in=["En attente", "Demande"]).exists():
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
       'demandes_pret': demandes_pret,
        "taux_change": taux_de_change,
        "max_possible_cdf": max_possible_cdf,
        "max_possible_usd": max_possible_usd,
    }

    return render(request, "membres/demande_pret.html", context)

login_required
@require_POST
@csrf_exempt
def payer_avance_pret(request, pret_id):
    try:
        data = json.loads(request.body)
        montant_avance = data.get('montant_avance')
        mot_de_passe = data.get('mot_de_passe')

        if not montant_avance or not mot_de_passe:
            return JsonResponse({'error': 'Le montant de l\'avance et le mot de passe sont requis.'}, status=400)

        try:
            montant_avance = Decimal(str(montant_avance))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Montant de l\'avance invalide (doit être un nombre).'}, status=400)

        if montant_avance <= 0:
            return JsonResponse({'error': 'Le montant de l\'avance doit être supérieur à zéro.'}, status=400)

        pret = get_object_or_404(
            Prets,
            membre=request.user.membre,
            pk=pret_id,
            statut='Approuvé'
        )

        if not check_password(mot_de_passe, request.user.password):
            return JsonResponse({'error': 'Mot de passe incorrect.'}, status=403)

        solde_restant_pret = pret.montant_payer - pret.solde_remboursé

        if montant_avance > solde_restant_pret:
            return JsonResponse({
                'error': f'Le montant de l\'avance ({montant_avance:.2f} {pret.devise}) est supérieur au solde restant du prêt ({solde_restant_pret:.2f} {pret.devise}).'
            }, status=400)

        membre = request.user.membre
        compte = membre.compte_USD if pret.devise == "USD" else membre.compte_CDF

        if compte.solde < montant_avance:
            return JsonResponse({'error': f'Solde insuffisant sur votre compte {pret.devise}.'}, status=400)

        with transaction.atomic():
            compte.solde -= montant_avance
            compte.save()

            Transactions.objects.create(
                membre=membre,
                montant=montant_avance,
                devise=pret.devise,
                type="paiement_avance_pret",
                statut="Approuvé",
                date_approbation=timezone.now()
            )

            pret.solde_remboursé += montant_avance

            montant_couvert_par_avance = montant_avance
            echeances_payees_cette_avance = 0

            echeances_a_payer = pret.echeances.filter(
                statut__in=['en_attente', 'en_retard', 'partiellement_payé']
            ).order_by('date_echeance')

            for echeance in echeances_a_payer:
                if montant_couvert_par_avance >= echeance.montant_du:
                   
                    montant_paye_pour_cette_echeance = echeance.montant_du
                    echeance.montant_du = Decimal('0.00') # Set remaining amount to zero
                    echeance.statut = 'payé'
                    echeance.date_paiement = timezone.now()
                    echeance.save()

                    montant_couvert_par_avance -= montant_paye_pour_cette_echeance
                    echeances_payees_cette_avance += 1

                    partager_benefices(pret, montant_paye_pour_cette_echeance)

                else:
                    montant_paye_pour_cette_echeance = montant_couvert_par_avance
                    echeance.montant_du -= montant_paye_pour_cette_echeance # Decrease the remaining amount
                    echeance.statut = 'partiellement_payé' # Mark as partially paid
                    echeance.save()

                    # Share profits for the PARTIAL amount paid for this installment
                    partager_benefices(pret, montant_paye_pour_cette_echeance)
                    
                    montant_couvert_par_avance = Decimal('0.00') # The advance is now exhausted
                    break # Exit loop as advance is fully used

            if pret.solde_remboursé >= pret.montant_payer:
                pret.statut = 'Remboursé'
                pret.date_remboursement = timezone.now()

            pret.save()

            return JsonResponse({
                'success': True,
                'message': f'Avance de {montant_avance:.2f} {pret.devise} effectuée avec succès ! {echeances_payees_cette_avance} échéance(s) entièrement payée(s). La dernière échéance a été ajustée si elle a été partiellement couverte.',
                'nouveau_solde_rembourse': pret.solde_remboursé,
                'solde_restant_pret': pret.montant_payer - pret.solde_remboursé,
                'pret_statut': pret.statut
            })

    except Prets.DoesNotExist:
        return JsonResponse({'error': 'Prêt introuvable ou non approuvé pour ce membre.'}, status=404)
    except Exception as e:
        print(f"Erreur inattendue dans payer_avance_pret: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Une erreur interne est survenue lors du paiement de l\'avance.'}, status=500)




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
@require_GET
@verifier_membre
def get_objectifs_by_status(request):
    try:      
        membre = request.user.membre
        status = request.GET.get('statut')
        
        objectifs = []
        if status and status != 'Tous':        
            objectifs = Objectifs.objects.filter(membre=membre, statut=status).order_by('-date_creation')
        else:
            objectifs = Objectifs.objects.filter(membre=membre).order_by('-date_creation')
            
        objectifs_data = []
        for objectif in objectifs:
            progress_percentage = 0
            try:
                if objectif.montant_cible is not None and objectif.montant_cible > 0:
                    montant = Decimal(str(objectif.montant))
                    montant_cible = Decimal(str(objectif.montant_cible))
                    progress_percentage = (montant / montant_cible) * 100
                else:
                    progress_percentage = 0
            except (InvalidOperation, TypeError, ZeroDivisionError) as e:                           
                progress_percentage = 0

            objectifs_data.append({
                'id': objectif.id,
                'nom': objectif.nom,
                'description': objectif.description if objectif.description is not None else '',
                'montant_cible': str(objectif.montant_cible) if objectif.montant_cible is not None else '0',
                'montant': str(objectif.montant) if objectif.montant is not None else '0',
                'devise': objectif.devise,
                'date_creation': objectif.date_creation.isoformat() if objectif.date_creation else None,
                'date_fin': objectif.date_fin.isoformat() if objectif.date_fin else None,
                'statut': objectif.statut,
                'progress_percentage': round(float(progress_percentage), 2),
            })       
        
        return JsonResponse({'objectifs': objectifs_data})

    except ObjectDoesNotExist as e:        
        return JsonResponse({'error': 'L\'objectif ou le membre demandé n\'existe pas.'}, status=404)
    except MultipleObjectsReturned as e:        
        return JsonResponse({'error': 'Plusieurs objectifs correspondent aux critères, ce qui est inattendu.'}, status=500)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': f'Une erreur interne est survenue: {e}'}, status=500)

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
        except ValueError:
            return JsonResponse({'error': 'Montant de dépôt invalide (doit être un nombre).'}, status=400)

       
        montant_restant_pour_cible = objectif.montant_cible - objectif.montant
        if montant_depot <= 0:
            return JsonResponse({'error': 'Le montant de dépôt doit être supérieur à zéro.'}, status=400)
        if montant_depot > montant_restant_pour_cible:
            return JsonResponse({
                'error': f'Le montant de dépôt ({montant_depot:.2f} {objectif.devise}) est supérieur au montant restant pour atteindre l\'objectif ({montant_restant_pour_cible:.2f} {objectif.devise}).'
            }, status=400)

       
        membre = request.user.membre
        compte = membre.compte_USD if objectif.devise == "USD" else membre.compte_CDF
        if compte.solde < Decimal(str(montant_depot)):
            return JsonResponse({'error': f'Solde insuffisant sur votre compte {objectif.devise}.'}, status=400)
       
        transaction = Transactions.objects.create(
            membre=membre,
            montant=montant_depot,
            devise=objectif.devise,
            type="depot_objectif",
            statut="Approuvé",
            date_approbation=timezone.now()
        )
       
        DepotsObjectif.objects.create(
            objectif=objectif,
            transaction=transaction,
            montant=montant_depot,
            devise=objectif.devise,
            statut="Approuvé",
            date_approbation=timezone.now()
        )

       
        objectif.montant += montant_depot
        if objectif.montant >= objectif.montant_cible:
            objectif.statut = "Atteint"
        objectif.save()

       
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
        return JsonResponse({'error': 'Objectif introuvable ou non "En cours".'}, status=404)
    except Exception as e:
       
        print(f"Une erreur inattendue est survenue: {e}")
        return JsonResponse({'error': 'Une erreur interne est survenue. Veuillez réessayer.'}, status=500)

# Vue pour retrait d'objectif
@login_required
@require_POST
@verifier_membre
def retrait_objectif(request, objectif_id):
    objectif = get_object_or_404(Objectifs, membre=request.user.membre, pk=objectif_id)
    membre = request.user.membre
    compte = membre.compte_USD if objectif.devise == "USD" else membre.compte_CDF

    try:
        data = json.loads(request.body)
        password = data.get('password')

        if not check_password(password, request.user.password):
            return JsonResponse({'success': False, 'error': 'Mot de passe incorrect.'}, status=400) # Changé status 400 à 403 pour plus de précision

        if objectif.montant == objectif.montant_cible:

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

            objectif.statut = "Retiré" 
            objectif.montant = Decimal('0.00')
            objectif.save()

            compte.solde += Decimal(str(objectif.montant_cible ))
            compte.save()

            return JsonResponse({'success': True, 'message': f"Retrait complet de {objectif.montant_cible} {objectif.devise} pour l'objectif '{objectif.nom}' effectué avec succès."})

        else:
            try:
                montant_retrait = Decimal(str(data.get('montant'))) 
                frais_retrait_objectif = Decimal('0.01') 

                if montant_retrait <= 0 or montant_retrait > objectif.montant:
                    return JsonResponse({'success': False, 'error': f'Montant de retrait invalide. Maximum: {objectif.montant} {objectif.devise}'}, status=400)
                
                # Calcul des montants
                montant_admin = montant_retrait * frais_retrait_objectif
                montant_membre = montant_retrait - montant_admin

                RetraitsObjectif.objects.create(
                    membre=membre,
                    objectif=objectif,
                    montant=montant_retrait, 
                    devise=objectif.devise,
                    statut="Approuvé",
                    transaction=Transactions.objects.create(
                        membre=membre,
                        montant=montant_membre, 
                        devise=objectif.devise,
                        type="retrait_objectif", 
                        statut="Approuvé",
                    )
                )
                
                BalanceAdmin.objects.create(
                    montant=montant_admin,
                    devise=objectif.devise,
                    type="Frais de retrait objectif" 
                )

                objectif.montant -= float(montant_retrait)
                
                compte.solde += montant_membre

                objectif.save()
                compte.save()

                return JsonResponse({
                    'success': True,
                    'message': f"Retrait de {montant_retrait} {objectif.devise} (frais de {montant_admin} {objectif.devise}). Vous avez reçu {montant_membre} {objectif.devise}.",
                    'nouveau_montant_objectif': str(objectif.montant), # Utile pour rafraîchir l'UI
                    'nouveau_solde_compte': str(compte.solde),
                    'devise': objectif.devise
                })
            except ValueError: 
                 return JsonResponse({'success': False, 'error': 'Montant de retrait invalide.'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f"Une erreur s'est produite lors du retrait partiel: {str(e)}"}, status=500)
                
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': "Données JSON invalides."}, status=400)
    except Objectifs.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Objectif introuvable ou ne vous appartient pas.'}, status=404)
    except Exception as e:
        # Cela attrape les erreurs générales qui ne sont pas gérées par les blocs try/except internes
        return JsonResponse({'success': False, 'error': f"Une erreur inattendue est survenue: {str(e)}"}, status=500)


@login_required
@verifier_membre
def archiver_objectif(request, objectif_id):
    membre = request.user.membre
    objectif = get_object_or_404(Objectifs, membre=membre, pk=objectif_id, statut__in=['En cours'], montant__lte=0 )

    try:
        data = json.loads(request.body)
        password = data.get('password')

        if not check_password(password, request.user.password):
            return JsonResponse({'success': False, 'error': 'Mot de passe incorrect.'}, status=400)

        objectif.statut = "Archivé"
        objectif.save()

        return JsonResponse({'success': True, 'message': f"Objectif '{objectif.nom}' archive avec succès"})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': "Données JSON invalides"}, status=400)
    except Objectifs.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Objectif introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST 
@login_required
@verifier_membre 
def reactiver_objectif(request, objectif_id):
    membre = request.user.membre
    try:
        objectif = get_object_or_404(
            Objectifs,
            membre=membre,
            pk=objectif_id,
            statut='Archivé' 
        )
    except Objectifs.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Objectif introuvable, non archivé ou ne vous appartient pas.'}, status=404)
    
    try:
        data = json.loads(request.body)
        password = data.get('password')

        if not check_password(password, request.user.password):
            return JsonResponse({'success': False, 'error': 'Mot de passe incorrect.'}, status=403) 

        objectif.statut = "En cours"
        objectif.save()

        return JsonResponse({'success': True, 'message': f"L'objectif '{objectif.nom}' a été réactivé avec succès."})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': "Données de requête invalides (JSON mal formé)."}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Une erreur inattendue s'est produite lors de la réactivation: {str(e)}"}, status=500)


# Vue pour la page de retrait du membre
@login_required
@verifier_membre
def benefices(request):
    membre = get_object_or_404(Membres, user=request.user)
    frais_retrais_benefice = 0.025

    #verfication s'il y a deja eu un retrait
    retraits = Retraits.objects.filter(membre=membre, statut="Approuvé")
    benefices = Benefices.objects.filter(membre=membre)

    montant_benefices_cdf = benefices_actuelle(membre, "CDF")
    montant_benefices_usd = benefices_actuelle(membre, "USD")

    if request.method == "POST":
        form = TransactionsForm(request.POST)

        if form.is_valid():
            transaction = form.save(commit=False)

            montant_benefices = montant_benefices_cdf if transaction.devise == "CDF" else montant_benefices_usd
            montant_recu = float(transaction.montant) * (1 - frais_retrais_benefice),
            montant_admin = float(transaction.montant) * frais_retrais_benefice

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
                BalanceAdmin.objects.create(
                        montant=montant_admin,
                        devise=transaction.devise,
                        type="Retrait benefice"
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
        "benefices":benefices,
        "ben"
        "membre": membre,
        "montant_benefices_cdf": montant_benefices_cdf,
        "montant_benefices_usd": montant_benefices_usd,
        "date": timezone.now()
    }

    return render(request, "membres/benefices.html", context)

# Vue pour la page de gestion des transferts du membre
@login_required
@verifier_membre 
def transfert(request):
    membre_connecte = request.user.membre
    transferts = Transferts.objects.filter(
        Q(membre_expediteur=membre_connecte) | Q(membre_destinataire=membre_connecte)
    ).order_by('-date')

    # Fetching 'id' along with other details for the autocomplete
    membres_destinataires_queryset = Membres.objects.exclude(user=request.user).values('pk', 'nom', 'prenom', 'numero_telephone')
    destinataires_js = [
        {
            'id': m['pk'],
            'nom_complet': f"{m['nom'].capitalize()} {m['prenom'].capitalize()}",
            'numero_telephone': m['numero_telephone']
        }
        for m in membres_destinataires_queryset
    ]

    if request.method == "POST":
        form = TransfertsForm(request.POST)
        if form.is_valid():
            montant = form.cleaned_data['montant']
            devise = form.cleaned_data['devise']
            motif = form.cleaned_data['motif']
            mot_de_passe = request.POST.get('mot_de_passe')
            destinataire_id = request.POST.get('destinataire_id') # Get the ID from the hidden input

            context = {
                    "form": form,
                    "membre": membre_connecte,
                    "transferts": transferts,
                    "membres_destinataires_json": json.dumps(destinataires_js),
                }

            # 1. Validate if a destinataire ID was provided by the frontend
            if not destinataire_id:
                messages.error(request, "Veuillez sélectionner un destinataire valide dans la liste.")
                return render(request, "membres/transfert.html",context )

            # 2. Try to retrieve the destinataire Membres object using the ID
            try:
                destinataire = Membres.objects.get(pk=destinataire_id)
            except Membres.DoesNotExist:
                messages.error(request, "Destinataire introuvable. Veuillez réessayer ou choisir un autre membre.")
                return render(request, "membres/transfert.html",context)
            except Exception as e:
                # Catch any other potential database errors
                messages.error(request, f"Une erreur s'est produite lors de la recherche du destinataire: {e}")
                return render(request, "membres/transfert.html",context)

            # 3. Verify the sender's password
            if check_password(mot_de_passe, request.user.password):
                try:
                    compte_expediteur = membre_connecte.compte_CDF if devise == "CDF" else membre_connecte.compte_USD
                    compte_destinataire = destinataire.compte_CDF if devise == "CDF" else destinataire.compte_USD

                    print(f"destinateur {compte_destinataire.solde} \n expeditaire {compte_expediteur.solde}")
                except AttributeError:
                    messages.error(request, "Erreur de configuration des comptes. Assurez-vous que les comptes CDF et USD sont liés à chaque membre.")
                    return render(request, "membres/transfert.html",context)

                # 4. Check sufficient balance
                if compte_expediteur.solde >= montant:
                    try:
                        # Create Transaction
                        transaction = Transactions.objects.create(
                            membre=membre_connecte,
                            montant=montant,
                            devise=devise,
                            type = "Transfert",
                            description=f"Transfert vers {destinataire.nom} {destinataire.prenom}",
                        )

                        # Create Transfer
                        transfert_obj = Transferts.objects.create( # Renamed variable to avoid conflict with queryset
                            transaction=transaction,
                            membre_expediteur=membre_connecte,
                            membre_destinataire=destinataire,
                            expediteur="membre",
                            destinataire="membre",
                            motif=motif,
                            montant=montant,
                            devise=devise,
                        )

                        # Update sender's balance
                        compte_expediteur.solde -= montant
                        compte_expediteur.save()

                        # Update recipient's balance
                        compte_destinataire.solde += montant
                        compte_destinataire.save()

                        messages.success(request, f"Transfert de {montant} {devise} effectué avec succès vers {destinataire.nom} {destinataire.prenom}.")
                        return redirect('membres:transfert')

                    except Exception as e:
                        messages.error(request, f"Une erreur inattendue s'est produite lors du transfert: {e}")
                else:
                    messages.error(request, "Solde insuffisant pour effectuer ce transfert.")
            else:
                messages.error(request, "Mot de passe incorrect.")
        else:
            # Form is not valid
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = TransfertsForm()

    return render(request, "membres/transfert.html", {
                    "form": form,
                    "membre": membre_connecte,
                    "transferts": transferts,
                    "membres_destinataires_json": json.dumps(destinataires_js),
                })


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
def transaction_detail(request, transaction_id):
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
                            
                            transaction=Transactions.objects.create(
                                membre=membre,
                                montant=montant_membre,
                                devise=devise,
                                type="retrait investissement",
                                
                            )
                        )

                        messages.success(request, "Retrait Investissement soumise avec succès.")
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

    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body.decode('utf-8'))
            montant = data.get('montant')
            devise = data.get('devise')
            mot_de_passe = data.get('password')
            numero = data.get('account_sender')
            fournisseur = data.get('fournisseur')

            if not check_password(mot_de_passe, request.user.password):
                return JsonResponse({'error': "Mot de passe incorrect."}, status=401)

            form = SoldeForm({'montant': montant, 'devise': devise, 'account_sender': numero})

            if form.is_valid():
                montant_decimal = form.cleaned_data['montant']
                devise_cleaned = form.cleaned_data['devise']
                numero_cleaned = form.cleaned_data['account_sender']
                net_montant = montant_decimal - (frais_retrait * montant_decimal)

                if montant_decimal <= 0:
                    return JsonResponse({'error': "Montant invalide."}, status=400)

                reference = f"TX-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                paiement_data = {
                    "numero": numero_cleaned,
                    "montant": float(montant_decimal),
                    "devise": devise_cleaned,
                    "reference": reference,
                    "fournisseur": fournisseur
                }

                # Appel à l'API de paiement
                if rechargerCompteService(paiement_data):
                    with db_transaction.atomic():
                        transaction = Transactions.objects.create(
                            membre=membre,
                            type="Rechargement compte",
                            montant=net_montant,
                            devise=devise_cleaned,
                            statut="Approuvé",
                            date_approbation=timezone.now()
                        )

                        Solde.objects.create(
                            transaction=transaction,
                            montant=net_montant,
                            devise=devise_cleaned,
                            account_sender=numero_cleaned,
                            frais_retrait=frais_retrait
                        )

                        # Crédit du compte
                        compte = membre.compte_USD if devise_cleaned == "USD" else membre.compte_CDF
                        compte.solde += net_montant
                        compte.save()

                    return JsonResponse({'success': True, 'message': "Rechargement effectué avec succès."}, status=200)
                else:
                    return JsonResponse({'error': "Échec du paiement. Veuillez réessayer."}, status=500)
            else:
                return JsonResponse({'errors': form.errors.as_json()}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': "Données JSON invalides."}, status=400)
        except Exception as e:
            return JsonResponse({'error': f"Une erreur inattendue s'est produite: {str(e)}"}, status=500)

    else:
        form = SoldeForm()
        return render(request, "membres/balance.html", {
            "form": form,
            "membre": membre,
        })