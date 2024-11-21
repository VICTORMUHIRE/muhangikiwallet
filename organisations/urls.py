from django.urls import path
from . import views

app_name = "organisations"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("contributions/", views.contributions, name="contributions"),
    path("prêts/", views.prêts, name="prêts"),
    path("types_prêt/", views.types_prêt, name="types_prêt"),
    path("modifier_type_prêt/<int:type_prêt_id>/", views.modifier_type_prêt, name="modifier_type_prêt"),
    path("supprimer_type_prêt/<int:type_prêt_id>/", views.supprimer_type_prêt, name="supprimer_type_prêt"),
    path("objectifs/", views.objectifs, name="objectifs"),
    path("creer_objectif/", views.creer_objectif, name="creer_objectif"),
    path("depot_objectif/<int:objectif_id>/", views.depot_objectif, name="depot_objectif"),
]