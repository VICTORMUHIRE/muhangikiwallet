from django.urls import path
from . import views

app_name = "membres"

urlpatterns = [
    path("", views.home, name="home"),
    path("balance/", views.balance, name="balance"),
    path("statut/", views.statut, name="statut"),
    path("inscription/", views.inscription, name="inscription"),
    path("password_reset/", views.password_reset, name="password_reset"),
    path("termes_et_conditions/", views.termes_et_conditions, name="termes_et_conditions"),
    path("retrait/", views.retrait, name="retrait"),
    path("transfert/", views.transfert, name="transfert"),
    path("contributions/", views.contributions, name="contributions"),
    path("transaction/<int:transaction_id>", views.transaction, name="transaction"),
    path("transactions/", views.transactions, name="transactions"),
    path("demande_pret/", views.demande_pret, name="demande_pret"),
    path("rembourser_pret/<int:transaction_id>", views.rembourser_pret, name="rembourser_pret"),
    path("objectifs/", views.objectifs, name="objectifs"),
    path("objectifs/depot/<int:objectif_id>", views.depot_objectif, name="depot_objectif"),
    path('objectifs/retrait/<int:objectif_id>', views.retrait_objectif, name='retrait_objectif'),
    path("objectifs/annuler/<int:objectif_id>", views.annulation_objectif, name="annulation_objectif"),
    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),
    path("parametres/", views.parametres, name="parametres"),
    path('get_villes/', views.get_villes, name='get_villes'),
    path('get_communes/', views.get_communes, name='get_communes'),
    path('get_quartiers/', views.get_quartiers, name='get_quartiers'),
    path('get_avenues/', views.get_avenues, name='get_avenues'),
    path("retirer_investissement/", views.retirer_investissement, name="retirer_investissement"),
    path('recharger/', views.recharger_compte, name='rechargeCompte'),
]
