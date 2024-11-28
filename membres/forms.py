from django import forms
from .models import Membres
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from administrateurs.models import CodesReference, Users


# Formulaire d'inscription de membre
class MembresForm(forms.ModelForm):
    # email = forms.EmailField()
    mot_de_passe = forms.CharField(widget=forms.PasswordInput())
    confirmation_mot_de_passe = forms.CharField(widget=forms.PasswordInput())
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
            "photo_passport",
            "province_residence",
            "ville_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_telephone",
            "contribution_mensuelle",
            "invitation_code",
        ]

        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"})
        }

    def clean(self):
        super().clean()

        mot_de_passe = self.cleaned_data.get("mot_de_passe")
        confirmation_mot_de_passe = self.cleaned_data.get("confirmation_mot_de_passe")
        code_invitation = self.cleaned_data.get("invitation_code")

        if mot_de_passe and confirmation_mot_de_passe and mot_de_passe != confirmation_mot_de_passe:
            self.add_error("confirmation_mot_de_passe", "Les mots de passe doivent correspondent")

        
        try: validate_password(mot_de_passe)
        except ValidationError as error:
            self.add_error("mot_de_passe", error)

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
    
