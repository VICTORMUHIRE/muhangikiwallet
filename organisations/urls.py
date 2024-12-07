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
    path("prets/", views.prets, name="prets"),
    path("types_pret/", views.types_pret, name="types_pret"),
    path("modifier_type_pret/<int:type_pret_id>/", views.modifier_type_pret, name="modifier_type_pret"),
    path("supprimer_type_pret/<int:type_pret_id>/", views.supprimer_type_pret, name="supprimer_type_pret"),
    path("objectifs/", views.objectifs, name="objectifs"),
    path("creer_objectif/", views.creer_objectif, name="creer_objectif"),
    path("depot_objectif/<int:objectif_id>/", views.depot_objectif, name="depot_objectif"),
]