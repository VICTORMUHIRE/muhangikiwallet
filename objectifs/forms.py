from django import forms
from .models import Objectifs, TypesObjectif

# Formulaire de création d'objectif
class ObjectifsForm(forms.ModelForm):
    class Meta:
        model = Objectifs
        fields = ["nom", "description", "montant_USD", "montant_CDF", "date_debut", "date_fin", "type_objectif"]

        widgets = {
            "date_debut": forms.DateInput(attrs={"type": "date"}),
            "date_fin": forms.DateInput(attrs={"type": "date"}),
        }

# Formulaire de type d'objectif
class TypesObjectifForm(forms.ModelForm):
    class Meta:
        model = TypesObjectif
        fields = ["name", "description"]
