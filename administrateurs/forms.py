from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Administrateurs, Constantes,SettingKeys



# Formulaire d'inscription d'administrateur
class AdministrateurForm(forms.ModelForm):
    mot_de_passe = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4 caractères minimum'}))
    confirmation_mot_de_passe = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4 caractères minimum'}))
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
            "photo_profile",
            "province_residence",
            "ville_residence",
            "commune_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_telephone",
            "status",
        ]

        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
            "numero_telephone": forms.TextInput(attrs={"placeholder": "Ex : +243999999999 ou 0999999999"}),
        }


    def clean(self):
        super().clean()

        numero_telephone = self.cleaned_data.get("numero_telephone")
        if Administrateurs.objects.filter(numero_telephone=numero_telephone).exists():
            self.add_error("numero_telephone", "Ce numéro de téléphone est déjà utilisé")

        mot_de_passe = self.cleaned_data.get("mot_de_passe")
        confirmation_mot_de_passe = self.cleaned_data.get("confirmation_mot_de_passe")

        if mot_de_passe and confirmation_mot_de_passe and mot_de_passe != confirmation_mot_de_passe:
            self.add_error("confirmation_mot_de_passe", "Les mots de passe doivent correspondre")

        return self.cleaned_data

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='Numéro de Téléphone', max_length=15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Entrez votre numéro de téléphone'})

class ConstantesForm(forms.ModelForm):
    class Meta:
        model = Constantes
        fields = ['key', 'value', 'description']

    def __init__(self, *args, **kwargs):
        super(ConstantesForm, self).__init__(*args, **kwargs)

        # Clé sous forme de dropdown (choix fixes)
        self.fields['key'].widget = forms.Select(choices=SettingKeys.choices)

        # Tu peux aussi personnaliser les widgets pour les autres champs si tu veux :
        self.fields['value'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez la valeur'})
        self.fields['description'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})