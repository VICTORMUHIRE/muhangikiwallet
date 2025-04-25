from django import forms

from .models import Solde, Transactions, Contributions, Retraits, DepotsObjectif, Transferts, Prets, TypesPret, DepotsInscription, Fidelites


# Formulaire de transaction
class TransactionsForm(forms.ModelForm):
    class Meta:
        model = Transactions
        fields = ["montant", "devise", "preuve", "numero_agent"]
        
        widgets = {
            "montant": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "devise": forms.Select(attrs={"class": "form-control form-select"}),
        }

class PretsForm(forms.ModelForm):
    class Meta:
        model = Prets
        fields = ["type_pret", "montant", "devise"]

# Formulaire de type de pret
class TypesPretForm(forms.ModelForm):
    class Meta:
        model = TypesPret
        fields = ["nom", "taux_interet", "delai_remboursement"]

class ContributionsForm(forms.ModelForm):
    class Meta:
        model = Contributions
        fields = ["montant", "devise"]

class RetraitsForm(forms.ModelForm):
    numero_agent = forms.CharField(max_length=20)
    class Meta:
        model = Retraits
        fields = ["montant", "devise"]

class DepotsObjectifForm(forms.ModelForm):
    class Meta:
        model = DepotsObjectif
        fields = ["objectif", "montant", "devise"]

class TransfertsForm(forms.ModelForm):
    numero_destinataire = forms.CharField(max_length=20)
    class Meta:
        model = Transferts
        fields = ["devise", "motif"]

class DepotsInscriptionForm(forms.ModelForm):
    class Meta:
        model = DepotsInscription
        fields = ["montant", "devise"]
        widgets = {
            "montant": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "devise": forms.Select(attrs={"class": "form-control form-select"}),
        }

class FidelitesForm(forms.ModelForm):
    class Meta:
        model = Fidelites
        fields = ["membre", "point", "transaction", "description"]

class SoldeForm(forms.ModelForm):

    class Meta:
        model = Solde
        fields = ['montant', 'devise', 'account_sender']
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant à déposer',
                'min': '0.01',
            }),
            'devise': forms.Select(attrs={
                'class': 'form-control',
            }),
            'account_sender': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de téléphone de l\'expéditeur',
            }),
        }
        labels = {
            'montant': 'Montant',
            'devise': 'Devise',
            'account_sender': 'Numéro de téléphone',
        }

    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        if montant <= 0:
            raise forms.ValidationError("Le montant doit être supérieur à 0.")
        return montant

    def clean_account_sender(self):
        numero = self.cleaned_data.get('account_sender')
        if not numero or len(numero) < 9:
            raise forms.ValidationError("Numéro de téléphone invalide.")
        return numero