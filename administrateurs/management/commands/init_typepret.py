from django.core.management.base import BaseCommand

from transactions.models import TypesPret

class Command(BaseCommand):
    '''  preremplir les types de pret'''

    def handle(self, *args, **options):
        types_prets = [
            {
                'nom': 'Prêts express',
                'description': 'Etre membre du système avec une ancienneté de 2 mois avec 3 historiques de recharge.',
                'taux_interet': 10.0000, # 10%
                'delais_traitement': 24, # moins de 24heures
                'delai_remboursement': 4, # 4 mois
                'investissement_min': None,
                'montant_min': None,
                'montant_max': None,
            },
            {
                'nom': 'Prêts commercial starter',
                'description': 'Etre membre du système avec une activité dans le activités suivantes (caféteriat, revendeur carburant, revendeur opérateur mobile, secrétariat public, Kiosque, petit commerçant de produit vivrier, mini-alimentation) avec un recharge de 10$ ou son équivalent en francs congolais.',
                'taux_interet': 5.0000,
                'delais_traitement': 72,
                'delai_remboursement': 6,
                'investissement_min': 10,
                'montant_min': 100,
                'montant_max': 300,
            },
            {
                'nom': 'Prêts commercial pro',
                'description': 'Etre membre du système avec une activités dans l’une des activités suivantes (Taxi moto, taxi voiture) avec une ancienneté de 3 mois avec 5 historiques de recharge et un solde d’investissement supérieur égale à 200$ ou son équivalent en francs congolais..',
                'taux_interet': 3.0000,
                'delais_traitement': 72,
                'delai_remboursement': 12,
                'investissement_min': 200,
                'montant_min': 1500.0000,
                'montant_max': 4500.0000,
            },
        ]

        self.stdout.write(self.style.NOTICE("Démarrage de l'insertion des types de prêt..."))

        for data in types_prets:
            try:
                obj, created = TypesPret.objects.get_or_create(
                    nom=data['nom'],
                    defaults={
                        'description': data['description'],
                        'taux_interet': data['taux_interet'],
                        'delais_traitement': data['delais_traitement'],
                        'delai_remboursement': data['delai_remboursement'],
                        'investissement_min': data['investissement_min'],
                        'montant_min': data['montant_min'],
                        'montant_max': data['montant_max'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Type de prêt '{obj.nom}' créé avec succès."))
                else:
                    self.stdout.write(self.style.WARNING(f"Type de prêt '{obj.nom}' existe déjà. Ignoré."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la création du type de prêt '{data['nom']}': {e}"))

        self.stdout.write(self.style.SUCCESS("Opération de seeding des types de prêt terminée."))