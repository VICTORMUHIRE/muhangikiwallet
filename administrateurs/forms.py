from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Administrateurs

# Formulaire d'inscription d'administrateur
class AdministrateurForm(forms.ModelForm):
    class Meta:
        model = Administrateurs
        fields = [
            "prenom",
            "nom",
            "postnom",
            "lieu_naissance",
            "date_naissance",
            "sexe",
            "type_carte_identite",
            "num_carte_identite",
            "photo_passport",
            "province_residence",
            "ville_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_telephone",
            "status",
        ]

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='Numéro de Téléphone', max_length=15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Entrez votre numéro de téléphone'})
