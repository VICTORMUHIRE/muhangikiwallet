from django import forms
from .models import Agents

# Formulaire d'inscription d'agent
class AgentsForm(forms.ModelForm):
    # email = forms.EmailField()
    mot_de_passe = forms.CharField(widget=forms.PasswordInput())
    confirmation_mot_de_passe = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = Agents
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
            "numero_telephone"
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

        
        # try: validate_password(mot_de_passe)
        # except ValidationError as error:
        #     pass
        #     self.add_error("mot_de_passe", error)

        if len(mot_de_passe) < 4:
            self.add_error("mot_de_passe", "Le mot de passe doit contenir au minimum 4 caractères")

        return self.cleaned_data

class ModifierAgentsForm(forms.ModelForm):
    class Meta:
        model = Agents
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
            "status"
        ]

        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"})
        }
