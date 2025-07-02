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
    path("benefices/", views.benefices, name="benefices"),
    path("transfert/", views.transfert, name="transfert"),
    path("contributions/", views.contributions, name="contributions"),

    # Routes API sous le préfixe /api/
    path('api/login/', views.api_login_view, name='api_login'),
    path("api/inscription/", views.api_inscription_membre, name="api_inscription_membre"),
    path('api/logout/', views.api_logout_view, name='api_logout'),
    path('api/checkpwd/', views. api_check_pwd_by_id, name='checkpwd'),
    path('api/recharger/', views.api_recharger_compte, name='recharge_api'),
    path('api/retirer/', views.api_retirer_compte, name='retrait_api'),
    path('api/transactions/<str:transaction_id>/status/', views.get_transaction_status, name='get_transaction_status'),

    # callback serdipay
    path('recharger/', views.serdipay_callback, name='serdipay_callback'),

    path("transaction/<int:transaction_id>", views.transaction_detail, name="transaction"),
    path("transactions/", views.transactions, name="transactions"),
    
    
    path("demande_pret/", views.demande_pret, name="demande_pret"),
    path('prets/payer-avance/<int:pret_id>/', views.payer_avance_pret, name='payer_avance_pret'),


    path("objectifs/", views.objectifs, name="objectifs"),
    path('api/objectifs/', views.get_objectifs_by_status, name='api_objectifs_by_status'),
    path("objectifs/depot/<int:objectif_id>", views.depot_objectif, name="depot_objectif"),
    path('objectifs/retrait/<int:objectif_id>', views.retrait_objectif, name='retrait_objectif'),
    path("objectifs/archiver/<int:objectif_id>", views.archiver_objectif, name="archiver_objectif"),
    path("objectifs/reactiver/<int:objectif_id>", views.reactiver_objectif, name="reactiver_objectif"),


    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),
    path("parametres/", views.parametres, name="parametres"),
    path('provinces/', views.get_provinces, name='get_provinces'),
    path('villes/', views.get_villes, name='get_villes'),
    path('communes/', views.get_communes, name='get_communes'),
    path('quartiers/', views.get_quartiers, name='get_quartiers'),
    path('avenues/', views.get_avenues, name='get_avenues'),
    path("retirer_investissement/", views.retirer_investissement, name="retirer_investissement"),
]
