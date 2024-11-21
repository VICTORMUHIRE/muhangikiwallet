from django.db import models
from django.conf import settings
from membres.models import Membres
from administrateurs.models import Provinces, Villes, Quartiers, Avenues
from django.conf import settings
from django.core.validators import RegexValidator

from django.utils.translation import gettext_lazy as _

# Définition du modèle d'organisation
class Organisations(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,  related_name='organisation', on_delete=models.CASCADE, primary_key=True)

    nom = models.CharField(max_length=255, verbose_name="Nom")
    
    id_national = models.CharField(max_length=255, verbose_name="Identifiant national")
    rccm = models.CharField(max_length=255, verbose_name="RCCM")
    impot = models.CharField(max_length=255, verbose_name="Impot")
    id_national_copy = models.CharField(max_length=255, verbose_name="Copie de l'identifiant national")

    province_residence = models.ForeignKey(Provinces, on_delete=models.CASCADE, verbose_name="Province de résidence")
    ville_residence = models.ForeignKey(Villes, on_delete=models.CASCADE, verbose_name="Ville de résidence")
    quartier_residence = models.ForeignKey(Quartiers, on_delete=models.CASCADE, verbose_name="Quartier de résidence")
    avenue_residence = models.ForeignKey(Avenues, on_delete=models.CASCADE, verbose_name="Avenue de résidence")
    numero_telephone = models.CharField(max_length=20, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Numéro de téléphone invalide.")], verbose_name="Numéro de téléphone")
    
    reference_code = models.CharField(max_length=45, verbose_name="Code de référence", blank=True, null=True)
    invitation_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="Code d'invitation")
    access_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="Code d'accès")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    compte_CDF = models.FloatField(default=0, verbose_name="Compte en CDF")
    compte_USD = models.FloatField(default=0, verbose_name="Compte en USD")

    status = models.BooleanField(default=False)

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = _("Organisation")
        verbose_name_plural = _("Organisations")
