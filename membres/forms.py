from django import forms
from .models import Membres
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from administrateurs.models import CodesReference, Users

# Formulaire d'inscription de membre
class MembresForm(forms.ModelForm):
    # email = forms.EmailField()
    mot_de_passe = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4 caractères minimum'}))
    confirmation_mot_de_passe = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4 caractères minimum'}))
    class Meta:
        model = Membres
        fields = [
            "nom",
            "postnom",
            "prenom",
            # "sexe",
            # "lieu_naissance",
            # "date_naissance",
            # "etat_civil",
            # "type_carte_identite",
            # "num_carte_identite",
            "carte_identite_copy",
            # "photo_profile",
            # "province_residence",
            # "ville_residence",
            # "commune_residence",
            # "quartier_residence",
            # "avenue_residence",
            # "numero_residence",
            "numero_telephone",
            # "contribution_mensuelle",
            # "invitation_code",
        ]

        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
            "numero_telephone": forms.TextInput(attrs={"placeholder": "Ex : +243999999999 ou 0999999999"}),
        }

    def clean(self):
        super().clean()

        numero_telephone = self.cleaned_data.get("numero_telephone")
        if Users.objects.filter(username=numero_telephone).exists():
            self.add_error("numero_telephone", "Ce numéro de téléphone est déjà utilisé")

        mot_de_passe = self.cleaned_data.get("mot_de_passe")
        confirmation_mot_de_passe = self.cleaned_data.get("confirmation_mot_de_passe")
        code_invitation = self.cleaned_data.get("invitation_code")

        if mot_de_passe and confirmation_mot_de_passe and mot_de_passe != confirmation_mot_de_passe:
            self.add_error("confirmation_mot_de_passe", "Les mots de passe doivent correspondent")

        # try: validate_password(mot_de_passe)
        # except ValidationError as error:
        #     pass
        #     # self.add_error("mot_de_passe", error)

        if len(mot_de_passe or "") < 4:
            self.add_error("mot_de_passe", "Le mot de passe doit contenir au minimum 4 caractères")

        code_invitation = self.cleaned_data.get("invitation_code")
        code_reference = CodesReference.objects.filter(code=code_invitation)
        
        if code_reference.exists():
            match code_reference.first().type:
                case "membre":
                    self.cleaned_data["invitation_code"] = code_reference.first().membre.numero_telephone
                case "organisation":
                    self.cleaned_data["invitation_code"] = code_reference.first().organisation.numero_telephone
                case "agent":
                    self.cleaned_data["invitation_code"] = code_reference.first().agent.numero_telephone
                case "administrateur":
                    self.cleaned_data["invitation_code"] = code_reference.first().administrateur.numero_telephone
                case _:
                    self.add_error("invitation_code", "Code d'invitation invalide")

        elif not Users.objects.filter(username=code_invitation).exists():
            self.add_error("invitation_code", "Code d'invitation invalide")

        return self.cleaned_data

class ModifierMembresForm(forms.ModelForm):
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
            #"carte_identite_copy",
            #"photo_profile",
            "province_residence",
            "ville_residence",
            "commune_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_residence",
            "numero_telephone",
            "contribution_mensuelle",
            "status"
        ]

        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
            "numero_telephone": forms.TextInput(attrs={"placeholder": "Ex : +243999999999 ou 0999999999"})
        }

