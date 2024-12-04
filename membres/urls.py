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
    path("contributions/depot", views.contribuer, name="contribuer"),
    path("transaction/<int:transaction_id>", views.transaction, name="transaction"),
    path("transactions/", views.transactions, name="transactions"),
    path("demande_prêt/", views.demande_prêt, name="demande_prêt"),
    path("rembourser_prêt/<int:transaction_id>", views.rembourser_prêt, name="rembourser_prêt"),
    path("objectifs/", views.objectifs, name="objectifs"),
    path("objectifs/dépot/<int:objectif_id>", views.dépot_objectif, name="dépot_objectif"),
    path("objectifs/voir/<int:objectif_id>", views.objectif, name="objectif"),
    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),
    path("paramètres/", views.paramètres, name="paramètres"),
]
