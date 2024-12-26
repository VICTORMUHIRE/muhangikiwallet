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
    path("admin/", admin.site.urls, name="admin"),
    path("agents/", include("agents.urls")),
    path("membres/", include("membres.urls")),
    path("organisations/", include("organisations.urls")),
    path("administrateurs/", include("administrateurs.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if __name__ == "__main__":
    from administrateurs.models import Administrateurs, Users, Provinces, Villes, Communes, Quartiers, Avenues, EtatsCivil, NumerosCompte, CodesReference, ContributionsMensuelles
    from transactions.models import Transactions, Prets, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices
    
    # Réinitialise tous les models
    Provinces.objects.all().delete()
    Villes.objects.all().delete()
    Communes.objects.all().delete()
    Quartiers.objects.all().delete()
    Avenues.objects.all().delete()
    EtatsCivil.objects.all().delete()
    NumerosCompte.objects.all().delete()
    CodesReference.objects.all().delete()
    ContributionsMensuelles.objects.all().delete()
    Administrateurs.objects.all().delete()
    Users.objects.all().delete()

    Transactions.objects.all().delete()
    Prets.objects.all().delete()
    TypesPret.objects.all().delete()
    Contributions.objects.all().delete()
    DepotsObjectif.objects.all().delete()
    Retraits.objects.all().delete()
    Transferts.objects.all().delete()
    DepotsInscription.objects.all().delete()
    Benefices.objects.all().delete()

    from objectifs.models import Objectifs
    Objectifs.objects.all().delete()

    from agents.models import Agents, NumerosAgent
    Agents.objects.all().delete()
    NumerosAgent.objects.all().delete()

    from membres.models import Membres
    Membres.objects.all().delete()

    from organisations.models import Organisations
    Organisations.objects.all().delete()


    if len(Administrateurs.objects.all()) == 0:
        # ContributionsMensuelles.objects.create(montant=1000, description="Contribution mensuelle minimale")
        # ContributionsMensuelles.objects.create(montant=2000, description="Contribution mensuelle maximale")
        # ContributionsMensuelles.objects.create(montant=5000, devise="USD", description="Contribution mensuelle maximale")

        # Provinces.objects.create(nom="Haut-Katanga")
        # Provinces.objects.create(nom="Kasaï")
        # Provinces.objects.create(nom="Kasaï-Central")
        Provinces.objects.create(nom="Nord-Kivu")
        Provinces.objects.create(nom="Sud-Kivu")

        Villes.objects.create(province=Provinces.objects.get(nom="Nord-Kivu"), nom="Goma")
        # Villes.objects.create(province=Provinces.objects.get(nom="Nord-Kivu"), nom="Butembo", type="Territoire")
        # Villes.objects.create(province=Provinces.objects.get(nom="Sud-Kivu"), nom="Bukavu")
        # Villes.objects.create(province=Provinces.objects.get(nom="Sud-Kivu"), nom="Uvira", type="Territoire")

        # Villes.objects.create(province=Provinces.objects.get(nom="Kasaï"), nom="Kananga")
        # Villes.objects.create(province=Provinces.objects.get(nom="Kasaï-Central"), nom="Mbuji-Mayi")
        # Villes.objects.create(province=Provinces.objects.get(nom="Haut-Katanga"), nom="Lubumbashi")

        # Communes.objects.create(ville=Villes.objects.get(nom="Lubumbashi"), nom="Kasongo")
        Communes.objects.create(ville=Villes.objects.get(nom="Goma"), nom="Goma")
        # Communes.objects.create(ville=Villes.objects.get(nom="Bukavu"), nom="Kadutu")
        # Communes.objects.create(ville=Villes.objects.get(nom="Uvira"), nom="Kasenga")

        # Quartiers.objects.create(commune=Communes.objects.get(nom="Kasongo"), nom="Kenya")
        # Quartiers.objects.create(commune=Communes.objects.get(nom="Kasongo"), nom="Kasongo")
        Quartiers.objects.create(commune=Communes.objects.get(nom="Goma"), nom="Kyeshero")
        # Quartiers.objects.create(commune=Communes.objects.get(nom="Kadutu"), nom="Kadutu")
        # Quartiers.objects.create(commune=Communes.objects.get(nom="Kasenga"), nom="Kasenga")

        # Avenues.objects.create(quartier=Quartiers.objects.get(nom="Kasongo"), nom="Kasongo")
        # Avenues.objects.create(quartier=Quartiers.objects.get(nom="Kenya"), nom="Kenya")
        Avenues.objects.create(quartier=Quartiers.objects.get(nom="Kyeshero"), nom="Douglas")
        # Avenues.objects.create(quartier=Quartiers.objects.get(nom="Kadutu"), nom="Kadutu")

        
        Administrateurs.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence=Provinces.objects.get(nom="Nord-Kivu"),
            commune_residence=Communes.objects.get(nom="Goma"),
            ville_residence=Villes.objects.get(nom="Goma"),
            quartier_residence=Quartiers.objects.get(nom="Kyeshero"),
            avenue_residence=Avenues.objects.get(nom="Douglas"),
            numero_telephone="0976465888", photo_profile="images/default.jpg",
            carte_identite_copy="images/default.jpg",
            user=Users.objects.create_user(
                username="0976465888",
                email="kakule@gmail.com",
                password="@!rm0n123#",
                first_name="Kakule",
                last_name="Rock",
                type="administrateur",
                is_staff=True,
                is_superuser=True
            )
        )

        ContributionsMensuelles.objects.create(montant=10)
        ContributionsMensuelles.objects.create(montant=100)

        agent = Agents.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence=Provinces.objects.get(nom="Nord-Kivu"),
            commune_residence=Communes.objects.get(nom="Goma"),
            ville_residence=Villes.objects.get(nom="Goma"),
            quartier_residence=Quartiers.objects.get(nom="Kyeshero"),
            avenue_residence=Avenues.objects.get(nom="Douglas"), numero_residence="123",
            numero_telephone="0999999999", photo_profile="images/default.jpg",
            carte_identite_copy="images/default.jpg",
            user=Users.objects.create_user(
                username="0999999999",
                email="kakule2@gmail.com",
                password="1234",
                first_name="Kakule",
                last_name="Rock",
                type="agent",
                is_staff=True
            )
        )

        NumerosAgent.objects.create(
            agent=agent,
            numero=agent.numero_telephone,
            reseau="Airtel"
        )

        membre = Membres.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence=Provinces.objects.get(nom="Nord-Kivu"),
            commune_residence=Communes.objects.get(nom="Goma"),
            ville_residence=Villes.objects.get(nom="Goma"),
            quartier_residence=Quartiers.objects.get(nom="Kyeshero"),
            avenue_residence=Avenues.objects.get(nom="Douglas"), numero_residence="123",
            numero_telephone="0999999998", photo_profile="images/default.jpg",
            carte_identite_copy="images/default.jpg", compte_CDF=NumerosCompte.objects.create(numero="MW-0000-0000-01", devise="CDF"),
            compte_USD=NumerosCompte.objects.create(numero="MW-0000-0000-02", devise="USD"),
            contribution_mensuelle=ContributionsMensuelles.objects.first(),
            user=Users.objects.create_user(
                username="0999999998",
                email="kakule2@gmail.com",
                password="1234",
                first_name="Kakule",
                last_name="Rock",
                type="membre"
            )
        )

        DepotsInscription.objects.create(membre=membre)