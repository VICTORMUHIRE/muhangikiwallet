from django.urls import path
from . import views

app_name = "agents"

urlpatterns = [
    path("", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("depot_inscription/", views.depot_inscription, name="depot_inscription"),

    path("voir_transaction/<int:transaction_id>/", views.voir_transaction, name="voir_transaction"),
    path("rejetter_transaction/<int:transaction_id>/", views.rejetter_transaction, name="rejetter_transaction"),
    path("prets/", views.prets, name="prets"),

    path("contributions/", views.contributions, name="contributions"),
    path("transactions/", views.transactions, name="transactions"),
    path("transaction/<int:transaction_id>", views.transaction, name="transaction")
]
