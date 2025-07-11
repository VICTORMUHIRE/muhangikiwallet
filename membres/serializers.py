from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from random import randint
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from .models import Membres, NumerosCompte
from administrateurs.models import  Users
from transactions.models import DepotsInscription

class MembreInscriptionSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=True) 
    mot_de_passe = serializers.CharField(write_only=True, required=True, min_length=8)
    confirmation_mot_de_passe = serializers.CharField(write_only=True, required=True, min_length=8)

    # Champs d'images, acceptant les fichiers
    photo_profile = serializers.ImageField(required=True)
    carte_identite_copy = serializers.ImageField(required=True)

    class Meta:
        model = Membres
        fields = [
            'prenom', 'nom', 'postnom', 'numero_telephone',
            'email', # Champ pour l'utilisateur
            'mot_de_passe', 'confirmation_mot_de_passe',
            'photo_profile', 'carte_identite_copy',
        ]

        extra_kwargs = {
            'prenom': {'required': True},
            'nom': {'required': True},
            'postnom': {'required': True},
            'numero_telephone': {'required': True},
        }

    def validate(self, data):
        if data['mot_de_passe'] != data['confirmation_mot_de_passe']:
            raise serializers.ValidationError({"confirmation_mot_de_passe": "Les mots de passe ne correspondent pas."})

        numero_telephone = data.get("numero_telephone")
        if Users.objects.filter(username=numero_telephone).exists():
            raise serializers.ValidationError({"numero_telephone": "Ce numéro de téléphone est déjà utilisé."})
        
        email = data.get("email")
        if Users.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Cet email est déjà utilisé."})

        # On ne passe pas confirmation_mot_de_passe au modèle
        data.pop('confirmation_mot_de_passe')

        return data

    # Fonction utilitaire pour générer un numéro de compte unique
    def generate_unique_numero(self):
        while True:
            numero = f"MW-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1, 99)).ljust(2, '0')}"
            if not NumerosCompte.objects.filter(numero=numero).exists():
                return numero

    @transaction.atomic
    def create(self, validated_data):
        # Retirer les données de l'utilisateur et des images pour les traiter séparément
        password = validated_data.pop('mot_de_passe')
        email = validated_data.pop('email')
        photo_profile_file = validated_data.pop('photo_profile')
        carte_identite_copy_file = validated_data.pop('carte_identite_copy')

        # Création de l'utilisateur (Users)
        user = Users.objects.create_user(
            username=validated_data['numero_telephone'],
            email=email,
            password=password,
            first_name=validated_data['nom'], # `nom` comme `first_name`
            last_name=validated_data['prenom'] or validated_data['postnom'], # `prenom` ou `postnom` comme `last_name`
            type="membre" # Assurez-vous que ce champ 'type' existe sur votre modèle Users
        )

        # Création des numéros de compte
        compte_cdf = NumerosCompte.objects.create(numero=self.generate_unique_numero(), devise="CDF")
        compte_usd = NumerosCompte.objects.create(numero=self.generate_unique_numero(), devise="USD")

        # Création du Membre
        membre = Membres.objects.create(
            user=user,
            compte_CDF=compte_cdf,
            compte_USD=compte_usd,
            # Assignation des autres champs directement depuis validated_data
            **validated_data
        )

        # Assigner et sauvegarder les fichiers images
        membre.photo_profile = photo_profile_file
        membre.carte_identite_copy = carte_identite_copy_file
        membre.save() # Sauvegarde les fichiers assignés

        DepotsInscription.objects.create(membre=membre)

        return membre


class RechargementSerializer(serializers.Serializer):
    """
    Serializer pour valider les données de rechargement de compte.
    """
    montant = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    devise = serializers.CharField(max_length=5) 
    account_sender = serializers.CharField(max_length=20) 
    fournisseur = serializers.CharField(max_length=10) 

    def validate_devise(self, value):
        if value.upper() not in ["USD", "CDF"]:
            raise serializers.ValidationError("La devise doit être 'USD' ou 'CDF'.")
        return value.upper()

    def validate_account_sender(self, value):
        fournisseur = self.initial_data.get('fournisseur', '').upper()
        numero = value.strip().replace(' ', '').replace('+', '')
    
        if not numero.startswith('243') or len(numero) != 12 or not numero.isdigit():
            raise serializers.ValidationError("Le numéro doit être au format +243 suivi de 9 chiffres, ex: +243970000000")
    
        prefix = numero[3:5]  # 2 premiers chiffres après 243
    
        prefix_mapping = {
            '0M': ['80', '84', '85', '89', '88'], 
            'AM': ['99', '97', '98'],    
            'MP': ['81', '82', '83', '86'],  
        }
    
        if fournisseur in prefix_mapping:
            if prefix not in prefix_mapping[fournisseur]:
                operateurs = {
                    'AM': 'Airtel',
                    'OM': 'Orange',
                    'MP': 'Vodacom',
                    'AF': 'Afrimoney'
                }
                raise serializers.ValidationError(
                    f"Le numéro ne correspond pas à {operateurs[fournisseur]}. Préfixes valides: {', '.join(prefix_mapping[fournisseur])}."
                )
        else:
            raise serializers.ValidationError("Fournisseur non reconnu pour la validation du numéro.")
    
        return numero


    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_password = request.data.get('mot_de_passe')

            if not check_password(user_password, request.user.password):
                raise serializers.ValidationError({"mot_de_passe": "Mot de passe incorrect."})
        else:
            raise serializers.ValidationError("Authentification requise.")
        return data # N'oubliez pas de