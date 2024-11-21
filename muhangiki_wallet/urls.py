from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from . import views
from django.conf.urls.static import static

app_name = "muhangiki_wallet"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin/", admin.site.urls),
    path("agents/", include("agents.urls")),
    path("membres/", include("membres.urls")),
    path("organisations/", include("organisations.urls")),
    path("administrateurs/", include("administrateurs.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if __name__ == "__main__"  and True:
    from administrateurs.models import ContributionsMensuelles, Administrateurs, NumerosCompte, CodesReference
    from agents.models import NumerosAgent, Agents
    from membres.models import Membres
    from transactions.models import TypesPrêt, Transactions, DepotsInscription
    from administrateurs.models import Users


    Users.objects.all().delete()
    Administrateurs.objects.all().delete()
    Membres.objects.all().delete()
    Agents.objects.all().delete()
    NumerosAgent.objects.all().delete()
    NumerosCompte.objects.all().delete()
    TypesPrêt.objects.all().delete()
    CodesReference.objects.all().delete()
    ContributionsMensuelles.objects.all().delete()
    Transactions.objects.all().delete()
    DepotsInscription.objects.all().delete()


    if len(Administrateurs.objects.all()) == 0:
        Administrateurs.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence="Nord-Kivu", ville_residence="Goma", quartier_residence="Kyeshero",
            avenue_residence="Douglas", numero_telephone="0909999999",
            user=Users.objects.create_user(
                username="0909999999",
                email="kakule@gmail.com",
                password="1234",
                first_name="Kakule",
                last_name="Rock",
                type="administrateur",
                is_staff=True,
                is_superuser=True
            
            )
        )

    if len(ContributionsMensuelles.objects.all()) == 0:
        ContributionsMensuelles.objects.create(montant=10, devise="USD")
        ContributionsMensuelles.objects.create(montant=20, devise="USD")
        ContributionsMensuelles.objects.create(montant=50, devise="USD")
        ContributionsMensuelles.objects.create(montant=100, devise="USD")
        ContributionsMensuelles.objects.create(montant=200, devise="USD")
        ContributionsMensuelles.objects.create(montant=300, devise="USD")
        ContributionsMensuelles.objects.create(montant=400, devise="USD")
        ContributionsMensuelles.objects.create(montant=500, devise="USD")
        ContributionsMensuelles.objects.create(montant=600, devise="USD")
        ContributionsMensuelles.objects.create(montant=700, devise="USD")
        ContributionsMensuelles.objects.create(montant=800, devise="USD")
        ContributionsMensuelles.objects.create(montant=900, devise="USD")
        ContributionsMensuelles.objects.create(montant=1000, devise="USD")

    if len(Membres.objects.all()) == 0:
        Agents.objects.create(
            nom="Kahambu", postnom="Nikuze", prenom="Sylvie",
            sexe="F", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence="Nord-Kivu", ville_residence="Goma", quartier_residence="Kyeshero",
            avenue_residence="Douglas", numero_telephone="0909899999",
            user=Users.objects.create_user(
                username="0909899999",
                email="kakule@gmail.com",
                password="1234",
                first_name="Kakule",
                last_name="Rock",
                type="agent",
            )
        )

    agent = Agents.objects.all()[0]

    if len(NumerosAgent.objects.all()) == 0:
        NumerosAgent.objects.create(
            numero="0909999999",
            reseau="Africel",
            agent=agent
        )

        NumerosAgent.objects.create(
            numero="0999999999",
            reseau="Airtel",
            agent=agent
        )

        NumerosAgent.objects.create(
            numero="0859999999",
            reseau="Orange",
            agent=agent
        )
        
        NumerosAgent.objects.create(
            numero="0819999999",
            reseau="Vodacom",
            agent=agent
        )

        Membres.objects.create(
            nom="Kavira", postnom="Kaghoma", prenom="Immaculée",
            sexe="F", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence="Nord-Kivu", ville_residence="Goma", quartier_residence="Kyeshero",
            avenue_residence="Douglas", numero_telephone="0909594999", compte_CDF=NumerosCompte.objects.create(numero="A1234567891", devise="CDF"),
            compte_USD=NumerosCompte.objects.create(numero="A1234567890", devise="USD"), invitation_code="INV1234567890",
            contribution_mensuelle=ContributionsMensuelles.objects.all()[0],
            reference_code=CodesReference.objects.create(), status=True,
            user=Users.objects.create_user(
                username="0909594999",
                email="kakule@gmail.com",
                password="1234",
                first_name="Kakule",
                last_name="Rock",
                type="membre"
            )
        )

        DepotsInscription.objects.create(
                transaction=Transactions.objects.create(
                    membre=Membres.objects.all().first(),
                    montant=10,
                    devise="USD",
                    type="depot_inscription",
                    agent=Agents.objects.all().first(),
                    numero_agent=NumerosAgent.objects.all().first(),
                    statut="Approuvé"
                )
            )


    if len(TypesPrêt.objects.all()) == 0:
        TypesPrêt.objects.create(nom="Express", taux_interet=10, delai_remboursement=30)
        TypesPrêt.objects.create(nom="Extended", taux_interet=15, delai_remboursement=60)
        TypesPrêt.objects.create(nom="Premium", taux_interet=20, delai_remboursement=90)
