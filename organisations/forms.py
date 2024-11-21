from django import forms
from .models import Organisations

# Formulaire d'inscription d'organisation
class OrganisationsForm(forms.ModelForm):
    class Meta:
        model = Organisations
        fields = [
            "nom",
            "id_national",
            "rccm",
            "impot",
            "id_national_copy",
            "province_residence",
            "ville_residence",
            "quartier_residence",
            "avenue_residence",
            "numero_telephone",
            "invitation_code",
            "access_code",
            "status",
        ]

        widgets = {
            "access_code": forms.TextInput(attrs={"readonly": "readonly"}),
        }
