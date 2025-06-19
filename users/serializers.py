from rest_framework import serializers
from .models import User
from .models import Membres, CodesReference, Users
from django.contrib.auth.password_validation import validate_password

class MembreSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, min_length=4)
    confirmation_mot_de_passe = serializers.CharField(write_only=True)

    class Meta:
        model = Membres
        fields = [
            "nom",
            "postnom",
            "prenom",
            "sexe",
            "lieu_naissance",
            "date_naissance",
            "etat_civil",
            "type_carte_identite",
            "num_carte_identite",
            "carte_identite_copy",
            "photo_profile",
            "province_residence",
            "ville_residence",
            "commune_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_residence",
            "numero_telephone",
            "contribution_mensuelle",
            "invitation_code",
            "mot_de_passe",
            "confirmation_mot_de_passe"
        ]

    def validate(self, data):
        """
        Cette méthode permet de faire des validations personnalisées.
        """

        # Vérifier si le mot de passe et sa confirmation correspondent
        if data.get("mot_de_passe") != data.get("confirmation_mot_de_passe"):
            raise serializers.ValidationError({"confirmation_mot_de_passe": "Les mots de passe doivent correspondre"})

        # Vérifier si le numéro de téléphone est déjà utilisé
        if Users.objects.filter(username=data.get("numero_telephone")).exists():
            raise serializers.ValidationError({"numero_telephone": "Ce numéro de téléphone est déjà utilisé"})

        # Vérifier la validité du mot de passe
        try:
            validate_password(data.get("mot_de_passe"))
        except serializers.ValidationError as error:
            raise serializers.ValidationError({"mot_de_passe": error.messages})

        # Vérifier le code d'invitation
        code_invitation = data.get("invitation_code")
        code_reference = CodesReference.objects.filter(code=code_invitation)

        if code_reference.exists():
            type_ref = code_reference.first().type
            if type_ref == "membre":
                data["invitation_code"] = code_reference.first().membre.numero_telephone
            elif type_ref == "organisation":
                data["invitation_code"] = code_reference.first().organisation.numero_telephone
            elif type_ref == "agent":
                data["invitation_code"] = code_reference.first().agent.numero_telephone
            elif type_ref == "administrateur":
                data["invitation_code"] = code_reference.first().administrateur.numero_telephone
            else:
                raise serializers.ValidationError({"invitation_code": "Code d'invitation invalide"})
        elif not Users.objects.filter(username=code_invitation).exists():
            raise serializers.ValidationError({"invitation_code": "Code d'invitation invalide"})

        return data

    def create(self, validated_data):
        """
        Cette méthode gère la création du membre et de l'utilisateur associé.
        """

        # Créer un utilisateur avec les informations validées
        user = Users.objects.create_user(
            username=validated_data["numero_telephone"],
            password=validated_data["mot_de_passe"],
            first_name=validated_data["nom"],
            last_name=validated_data["prenom"] or validated_data["postnom"],
            type="membre"
        )

        # Créer un membre
        membre = Membres.objects.create(
            user=user,
            nom=validated_data["nom"],
            postnom=validated_data["postnom"],
            prenom=validated_data["prenom"],
            sexe=validated_data["sexe"],
            lieu_naissance=validated_data["lieu_naissance"],
            date_naissance=validated_data["date_naissance"],
            etat_civil=validated_data["etat_civil"],
            type_carte_identite=validated_data["type_carte_identite"],
            num_carte_identite=validated_data["num_carte_identite"],
            carte_identite_copy=validated_data["carte_identite_copy"],
            photo_profile=validated_data["photo_profile"],
            province_residence=validated_data["province_residence"],
            ville_residence=validated_data["ville_residence"],
            commune_residence=validated_data["commune_residence"],
            quartier_residence=validated_data["quartier_residence"],
            avenue_residence=validated_data["avenue_residence"],
            numero_residence=validated_data["numero_residence"],
            numero_telephone=validated_data["numero_telephone"],
            contribution_mensuelle=validated_data["contribution_mensuelle"],
            invitation_code=validated_data["invitation_code"]
        )

        # Créer des comptes
        def generate_unique_numero():
            while True:
                numero = f"MW-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1000, 9999)).ljust(4, '0')}-{str(randint(1, 99)).ljust(2, '0')}"
                if not NumerosCompte.objects.filter(numero=numero).exists():
                    break
            return numero

        membre.compte_CDF = NumerosCompte.objects.create(numero=generate_unique_numero(), devise="CDF")
        membre.compte_USD = NumerosCompte.objects.create(numero=generate_unique_numero(), devise="USD")
        membre.save()

        # Créer un dépôt d'inscription pour le membre
        DepotsInscription.objects.create(membre=membre)

        return membre

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}  # Le mot de passe doit être seulement en écriture

    def create(self, validated_data):
        user = User.objects.create_user(          
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
