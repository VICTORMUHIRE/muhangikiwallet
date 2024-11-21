from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from transactions.models import Transactions, Prêts, TypesPrêt
from .models import Organisations
from .forms import OrganisationsForm
from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm

# Vue pour la page d'accueil des organisations
@login_required
def home(request):
    organisation = request.user.organisation

    # Solde disponible de l'organisation
    solde_CDF = organisation.compte_CDF
    solde_USD = organisation.compte_USD

    # Calcul du montant total des prêts accordés à l'organisation
    total_prêts_CDF = Prêts.objects.filter(organisation=organisation, devise="CDF", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0
    total_prêts_USD = Prêts.objects.filter(organisation=organisation, devise="USD", statut="Approuvé").aggregate(Sum('montant'))['montant__sum'] or 0

    # Récupérer les 4 dernières transactions de l'organisation
    transactions = Transactions.objects.filter(organisation=organisation).order_by('-date')[:4]

    # Récupérer tous les membres de l'organisation
    membres = organisation.membres_set.all()  # Accédez aux membres via la relation inverse

    context = {
        'solde_CDF': solde_CDF,
        'solde_USD': solde_USD,
        'total_prêts_CDF': total_prêts_CDF,
        'total_prêts_USD': total_prêts_USD,
        'transactions': transactions,
        'membres': membres,
    }
    return render(request, "organisations/home.html", context)

# Vue pour la page de connexion des organisations
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_organisation:  # Vérifier si l'utilisateur est une organisation
                login(request, user)
                return redirect("organisations:home")
            else:
                messages.error(request, "Vous n'êtes pas autorisé à accéder à cette page.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = AuthenticationForm()
    return render(request, "organisations/login.html", {"form": form})

# Vue pour la page de déconnexion des organisations
def logout_view(request):
    logout(request)
    return redirect("organisations:login")

# Vue pour la page d'inscription des organisations
def register(request):
    if request.method == "POST":
        form = OrganisationsForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.type = 'organisation'  # Définir le type d'utilisateur comme 'organisation'
            user.save()
            messages.success(request, "Votre inscription a été effectuée avec succès. Vous pouvez maintenant vous connecter.")
            return redirect("organisations:login")
    else:
        form = OrganisationsForm()
    return render(request, "organisations/register.html", {"form": form})

# Vue pour la page de profil de l'organisation
@login_required
def profile(request):
    organisation = request.user.organisations
    if request.method == "POST":
        form = OrganisationsForm(request.POST, request.FILES, instance=organisation)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour avec succès.")
            return redirect("organisations:profile")
    else:
        form = OrganisationsForm(instance=organisation)
    context = {
        "form": form,
        "organisation": organisation,
    }
    return render(request, "organisations/profile.html", context)

# Vue pour la page de gestion des membres (à implémenter)
@login_required
def membres(request):
    organisation = request.user.organisations
    membres = organisation.membres_set.all()  # Accédez aux membres via la relation inverse
    context = {
        "membres": membres,
    }
    return render(request, "organisations/membres.html", context)

# Vue pour la page de gestion des types de prêt (à implémenter)
@login_required
def types_prêt(request):
    types_prêt = TypesPrêt.objects.all()
    context = {
        "types_prêt": types_prêt,
    }
    return render(request, "organisations/types_prêt.html", context)

# Vue pour la page de modification d'un type de prêt (à implémenter)
@login_required
def modifier_type_prêt(request, type_prêt_id):
    type_prêt = get_object_or_404(TypesPrêt, pk=type_prêt_id)
    # Logique pour modifier le type de prêt
    return render(request, "organisations/modifier_type_prêt.html")

# Vue pour la page de suppression d'un type de prêt (à implémenter)
@login_required
def supprimer_type_prêt(request, type_prêt_id):
    type_prêt = get_object_or_404(TypesPrêt, pk=type_prêt_id)
    # Logique pour supprimer le type de prêt
    return redirect("organisations:types_prêt")

# Vue pour la page de gestion des prêts (à implémenter)
@login_required
def prêts(request):
    prêts = Prêts.objects.all()
    context = {
        "prêts": prêts,
    }
    return render(request, "organisations/prêts.html", context)

# Vue pour la page de gestion des transactions (à implémenter)
@login_required
def transactions(request):
    organisation = request.user.organisations
    transactions = Transactions.objects.filter(organisation=organisation).order_by('-date')
    context = {
        "transactions": transactions,
    }
    return render(request, "organisations/transactions.html", context)

@login_required
def contributions(request):
    return render(request, "organisations/contributions.html")

@login_required
def objectifs(request):
    return render(request, "organisations/objectifs.html")

@login_required
def creer_objectif(request):
    return render(request, "organisations/creer_objectif.html")

@login_required
def depot_objectif(request, objectif_id):
    return render(request, "organisations/depot_objectif.html")
