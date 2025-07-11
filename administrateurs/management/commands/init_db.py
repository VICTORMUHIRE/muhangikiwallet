from django.core.management.base import BaseCommand
from administrateurs.models import Administrateurs, Users, Provinces, Villes, Communes, Quartiers, Avenues, EtatsCivil, NumerosCompte, CodesReference, ContributionsMensuelles
from transactions.models import Transactions, Prets, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts, DepotsInscription, Benefices, RetraitsAdmin, BalanceAdmin
from objectifs.models import Objectifs
from agents.models import Agents, NumerosAgent
from membres.models import Membres
from organisations.models import Organisations

class Command(BaseCommand):
    help = 'Initialise la base de données avec des données par défaut'

    def handle(self, *args, **kwargs):
        # Réinitialisation
        models = [
            Provinces, Villes, Communes, Quartiers, Avenues, EtatsCivil, NumerosCompte,
            CodesReference, ContributionsMensuelles, Administrateurs, Users, Transactions,
            Prets, TypesPret, Contributions, DepotsObjectif, Retraits, Transferts,
            DepotsInscription, Benefices, RetraitsAdmin, BalanceAdmin, Objectifs,
            Agents, NumerosAgent, Membres, Organisations
        ]
        for model in models:
            model.objects.all().delete()

        nord_kivu = Provinces.objects.create(nom="Nord-Kivu")
        sud_kivu = Provinces.objects.create(nom="Sud-Kivu")
        goma = Villes.objects.create(province=nord_kivu, nom="Goma")
        commune = Communes.objects.create(ville=goma, nom="Goma")
        quartier = Quartiers.objects.create(commune=commune, nom="Kyeshero")
        avenue = Avenues.objects.create(quartier=quartier, nom="Douglas")

        contrib1 = ContributionsMensuelles.objects.create(montant=10)
        contrib2 = ContributionsMensuelles.objects.create(montant=100)

        user_admin = Users.objects.create_user(
            username="0999999888", email="kakule@gmail.com",
            password="12345", first_name="Kakule",
            last_name="Rock", type="administrateur",
            is_staff=True, is_superuser=True
        )
        Administrateurs.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence=nord_kivu, ville_residence=goma, commune_residence=commune,
            quartier_residence=quartier, avenue_residence=avenue,
            numero_telephone="0999999888", photo_profile="images/default.jpg",
            carte_identite_copy="images/default.jpg", user=user_admin
        )

        user_agent = Users.objects.create_user(
            username="0999999999", email="kakule2@gmail.com",
            password="1234", first_name="Kakule", last_name="Rock",
            type="agent", is_staff=True
        )
        agent = Agents.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence=nord_kivu, ville_residence=goma, commune_residence=commune,
            quartier_residence=quartier, avenue_residence=avenue,
            numero_residence="123", numero_telephone="0999999999",
            photo_profile="images/default.jpg", carte_identite_copy="images/default.jpg",
            user=user_agent
        )
        NumerosAgent.objects.create(agent=agent, numero=agent.numero_telephone, reseau="Airtel")

        compte_cdf = NumerosCompte.objects.create(numero="MW-0000-0000-01", devise="CDF")
        compte_usd = NumerosCompte.objects.create(numero="MW-0000-0000-02", devise="USD")
        user_membre = Users.objects.create_user(
            username="0999999998", email="kakule3@gmail.com",
            password="1234", first_name="Kakule", last_name="Rock",
            type="membre"
        )
        membre = Membres.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence=nord_kivu, ville_residence=goma, commune_residence=commune,
            quartier_residence=quartier, avenue_residence=avenue, numero_residence="123",
            numero_telephone="0999999998", photo_profile="images/default.jpg",
            carte_identite_copy="images/default.jpg", compte_CDF=compte_cdf, compte_USD=compte_usd,
            contribution_mensuelle=contrib1, user=user_membre
        )
        DepotsInscription.objects.create(membre=membre)

        self.stdout.write(self.style.SUCCESS("✅ Données initiales insérées avec succès."))
