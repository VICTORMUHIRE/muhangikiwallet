from django.urls import path
from . import views

app_name = "membres"

urlpatterns = [
    path("", views.home, name="home"),
    path("statut/", views.statut, name="statut"),
    path("inscription/", views.inscription, name="inscription"),
    path("password_reset/", views.password_reset, name="password_reset"),
    path("termes_et_conditions/", views.termes_et_conditions, name="termes_et_conditions"),
    path("retrait/", views.retrait, name="retrait"),
    path("transfert/", views.transfert, name="transfert"),
    path("contributions/", views.contributions, name="contributions"),
    path("transactions/", views.transactions, name="transactions"),
    path("demande_prêt/", views.demande_prêt, name="demande_prêt"),
    path("objectifs/", views.objectifs, name="objectifs"),
    path("profil/", views.profil, name="profil"),
    path("notifications/", views.notifications, name="notifications"),
    path("paramètres/", views.paramètres, name="paramètres"),
]
