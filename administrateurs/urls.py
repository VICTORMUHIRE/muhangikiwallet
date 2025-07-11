from django.urls import path, re_path
from . import views

app_name = "administrateurs"

urlpatterns = [
    path("", views.home, name="home"),
    path("profile/", views.profile, name="profile"),

    path("membres/", views.membres, name="membres"),
    path("membres/creer/", views.creer_membre, name="creer_membre"),
    path("membres/<int:membre_id>/", views.voir_membre, name="voir_membre"),
    path("membres/<int:membre_id>/modifier/", views.modifier_membre, name="modifier_membre"),
    path("membres/<int:membre_id>/supprimer/", views.supprimer_membre, name="supprimer_membre"),
    path("membres/<int:membre_id>/accepter/", views.accepter_membre, name="accepter_membre"),
    path("membres/<int:membre_id>/refuser/", views.refuser_membre, name="refuser_membre"),

    path("agents/", views.agents, name="agents"),
    path("agents/creer/", views.creer_agent, name="creer_agent"),
    path("agents/<int:agent_id>/", views.voir_agent, name="voir_agent"),
    path("agents/<int:agent_id>/modifier/", views.modifier_agent, name="modifier_agent"),
    path("agents/<int:agent_id>/supprimer/", views.supprimer_agent, name="supprimer_agent"),

    path("objectifs/", views.objectifs, name="objectifs"),
    path("retrait/", views.retrait, name="retrait"),
    
    path("transactions/", views.transactions, name="transactions"),
    path("transaction/<int:transaction_id>", views.transaction, name="transaction"),
    
    path("prets/", views.prets, name="prets"),
    path("prets/<int:pret_id>", views.voir_pret, name="voir_pret"),
    path("rejeter_pret/<int:pret_id>", views.rejeter_pret, name="rejeter_pret"),

    path("retraits/<int:retrait_id>", views.valider_retrait_investissement, name="voir_retrait"),
    path("rejeter_retrait/<int:retrait_id>", views.rejeter_retrait, name="rejeter_retrait"),

    path("demande_retrait_tout/<int:retrait_id>", views.demande_retrait_tout, name="demande_retrait_tout"),
    path("refuser_retrait_tout/<int:retrait_id>", views.refuser_retrait_tout, name="refuser_retrait_tout"),


    path("constantes", views.constantes, name="constantes"),

    path('types_pret/', views.liste_types_pret, name='liste_types_pret'), 
    path('types_pret/api/<int:pk>/modifier/', views.modifier_type_pret, name='modifier_type_pret_ajax'),


]
