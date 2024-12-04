from django.urls import path
from . import views

app_name = "agents"

urlpatterns = [
    path("", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("depot_inscription/", views.depot_inscription, name="depot_inscription"),

    # path("transactions/<int:transaction_id>/", views.voir_transaction, name="voir_transaction"),
    # path("transactions/<int:transaction_id>/approuver/", views.approuver_transaction, name="approuver_transaction"),
    # path("transactions/<int:transaction_id>/rejetter/", views.rejetter_transaction, name="rejetter_transaction"),
    # path("prêts/<int:prêt_id>/", views.voir_prêt, name="voir_prêt"),
    # path("prêts/<int:prêt_id>/approuver/", views.approuver_prêt, name="approuver_prêt"),
    # path("prêts/<int:prêt_id>/rejetter/", views.rejetter_prêt, name="rejetter_prêt"),
    # path("objectifs/<int:objectif_id>/", views.voir_objectif, name="voir_objectif"),
    # path("retraits/<int:retrait_id>/", views.voir_retrait, name="voir_retrait"),
    # path("retraits/<int:retrait_id>/approuver/", views.approuver_retrait, name="approuver_retrait"),
    # path("retraits/<int:retrait_id>/rejetter/", views.rejetter_retrait, name="rejetter_retrait"),

    path("voir_transaction/<int:transaction_id>/", views.voir_transaction, name="voir_transaction"),
    path("depot_inscription/approuver/<int:transaction_id>/", views.approuver_depot_inscription, name="approuver_depot_inscription"),
    path("depot_inscription/rejetter/<int:transaction_id>/", views.rejetter_depot_inscription, name="rejetter_depot_inscription"),

    path("contributions/", views.contributions, name="contributions"),
    path("transactions/", views.transactions, name="transactions"),
    path("transaction/<int:transaction_id>", views.transaction, name="transaction"),
    path("prêts/", views.prêts, name="prêts"),
    path("objectifs/", views.objectifs, name="objectifs"),
    path("retraits/", views.retraits, name="retraits"),
    path("parametres/", views.parametres, name="parametres")
]
