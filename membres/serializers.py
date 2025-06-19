from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from random import randint
from django.utils import timezone


from .models import Membres, NumerosCompte
from administrateurs.models import CodesReference, Users
from transactions.models import DepotsInscription

User = get_user_model()

class MembreRegistrationSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirmation_mot_de_passe = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Membres
        fields = [
            "nom", "postnom", "prenom", "sexe", "lieu_naissance", "date_naissance",
            "etat_civil", "type_carte_identite", "num_carte_identite",
            "carte_identite_copy", "photo_profile",
            "province_residence", "ville_residence", "commune_residence",
            "quartier_residence", "avenue_residence", "numero_residence",
            "numero_telephone", "invitation_code",
            "mot_de_passe", "confirmation_mot_de_passe",
        ]
        read_only_fields = ['user', 'compte_CDF', 'compte_USD']

    def validate(self, data):
        numero_telephone = data.get("numero_telephone")
        if User.objects.filter(username=numero_telephone).exists():
            raise serializers.ValidationError({"numero_telephone": "Ce numéro de téléphone est déjà utilisé."})

        mot_de_passe = data.get("mot_de_passe")
        confirmation_mot_de_passe = data.get("confirmation_mot_de_passe")
        if mot_de_passe != confirmation_mot_de_passe:
            raise serializers.ValidationError({"confirmation_mot_de_passe": "Les mots de passe doivent correspondre."})

        if len(mot_de_passe or "") < 4:
            raise serializers.ValidationError({"mot_de_passe": "Le mot de passe doit contenir au minimum 4 caractères."})

        code_invitation = data.get("invitation_code")
        code_reference = CodesReference.objects.filter(code=code_invitation).first()
        
        if code_reference:
            if code_reference.type == "membre" and hasattr(code_reference, 'membre') and code_reference.membre:
                data["invitation_code"] = code_reference.membre.numero_telephone
            elif code_reference.type == "organisation" and hasattr(code_reference, 'organisation') and code_reference.organisation:
                data["invitation_code"] = code_reference.organisation.numero_telephone
            elif code_reference.type == "agent" and hasattr(code_reference, 'agent') and code_reference.agent:
                data["invitation_code"] = code_reference.agent.numero_telephone
            elif code_reference.type == "administrateur" and hasattr(code_reference, 'administrateur') and code_reference.administrateur:
                data["invitation_code"] = code_reference.administrateur.numero_telephone
            else:
                raise serializers.ValidationError({"invitation_code": "Type de code d'invitation invalide ou lié à un objet inexistant."})
        elif not User.objects.filter(username=code_invitation).exists():
            raise serializers.ValidationError({"invitation_code": "Code d'invitation invalide."})
        
        return data

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['numero_telephone'],
                password=validated_data['mot_de_passe'],
                first_name=validated_data['nom'],
                last_name=validated_data.get('postnom') or validated_data.get('prenom'),
                type="membre"
            )
            
            validated_data.pop('mot_de_passe')
            validated_data.pop('confirmation_mot_de_passe')

            membre = Membres.objects.create(user=user, **validated_data)

            def generate_unique_numero():
                while True:
                    numero = f"MW-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1, 99)).ljust(2, '0')}"
                    if not NumerosCompte.objects.filter(numero=numero).exists():
                        return numero
            
            membre.compte_CDF = NumerosCompte.objects.create(numero=generate_unique_numero(), devise="CDF")
            membre.compte_USD = NumerosCompte.objects.create(numero=generate_unique_numero(), devise="USD")
            membre.save()

            membre.mois_contribution = timezone.now().replace(day=15)
            membre.save()

            DepotsInscription.objects.create(membre=membre)

            return membre
