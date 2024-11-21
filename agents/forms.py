from django import forms
from .models import Agents

# Formulaire d'inscription d'agent
class AgentsForm(forms.ModelForm):
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
            "photo_profil",
            "province_residence",
            "ville_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_telephone",
            "status",
        ]
