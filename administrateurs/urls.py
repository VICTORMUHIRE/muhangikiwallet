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
    path("agents/creer/", views.creer_agent, name="creer_agent"), # Assuming you have these views
    path("agents/<int:agent_id>/", views.voir_agent, name="voir_agent"), # Similar to membre views
    path("agents/<int:agent_id>/modifier/", views.modifier_agent, name="modifier_agent"),
    path("agents/<int:agent_id>/supprimer/", views.supprimer_agent, name="supprimer_agent"),

    path("organisations/", views.organisations, name="organisations"),
    path("organisations/creer/", views.creer_organisation, name="creer_organisation"),
    path("organisations/<int:organisation_id>/", views.voir_organisation, name="voir_organisation"), # Add a view for this
    path("organisations/<int:organisation_id>/modifier/", views.modifier_organisation, name="modifier_organisation"),
    path("organisations/<int:organisation_id>/supprimer/", views.supprimer_organisation, name="supprimer_organisation"),

    path("administrateurs/", views.administrateurs, name="administrateurs"),
    path("administrateurs/creer/", views.creer_administrateur, name="creer_administrateur"), # Add a view for this
    path("administrateurs/<int:administrateur_id>/", views.voir_administrateur, name="voir_administrateur"), # Add a view for this
    path("administrateurs/<int:administrateur_id>/modifier/", views.modifier_administrateur, name="modifier_administrateur"), # Add a view for this
    path("administrateurs/<int:administrateur_id>/supprimer/", views.supprimer_administrateur, name="supprimer_administrateur"), # Add a view for this
    
    path("transactions/cdf/creer/", views.creer_transaction_cdf, name="creer_transaction_cdf"),
    path("transactions/usd/creer/", views.creer_transaction_usd, name="creer_transaction_usd"),

    path("types_prêt/", views.types_prêt, name="types_prêt"),
    path("types_prêt/creer/", views.creer_type_prêt, name="creer_type_prêt"),
    path("types_prêt/<int:type_prêt_id>/modifier/", views.modifier_type_prêt, name="modifier_type_prêt"),
    path("types_prêt/<int:type_prêt_id>/supprimer/", views.supprimer_type_prêt, name="supprimer_type_prêt"),

    path("transactions/", views.transactions, name="transactions"), # If you have views for this
    path("prêts/", views.prêts, name="prêts"),
    path("prêts/<int:transaction_id>", views.voir_prêt, name="voir_prêt"),
    path("rejeter_prêt/<int:prêt_id>", views.rejeter_prêt, name="rejeter_prêt"),
]