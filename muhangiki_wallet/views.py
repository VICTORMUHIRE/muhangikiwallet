from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from administrateurs.forms import CustomLoginForm
from django.contrib.auth import login, logout

@login_required
def index(request):
    match request.user.type:
        case "administrateur":
            return redirect("administrateurs:home")
        case "agent":
            return redirect("agents:home")
        case "membre":
            return redirect("membres:home")
        case "organisation":
            return redirect("organisations:home")
        case _:
            return redirect("login")

# Vue pour la page de connexion des membres
def login_view(request):
    # Vérifier si l'utilisateur est déjà connecté
    if request.user.is_authenticated: return redirect("index")
    
    # messages.get_messages(request).clear()
    
    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.POST.get("next") or "index")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")
    
    form = CustomLoginForm()
    return render(request, "login.html", {"form": form})

# Vue pour la page de déconnexion des membres
def logout_view(request):
    logout(request)
    return redirect("login")
