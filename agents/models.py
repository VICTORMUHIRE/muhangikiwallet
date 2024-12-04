from django.db import models
from django.conf import settings
from administrateurs.models import Provinces, Villes, Quartiers, Avenues, EtatsCivil, TypesCarteIdentite, CodesReference, TYPES_CARTE_IDENTITE
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
    
# Définition du modèle d'agent
class Agents(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="agent", on_delete=models.CASCADE, primary_key=True)
    
    nom = models.CharField(max_length=20, verbose_name="Nom")
    postnom = models.CharField(max_length=20, verbose_name="Postnom")
    prenom = models.CharField(max_length=20, blank=True, null=True, verbose_name="Prénom")
    
    sexe = models.CharField(max_length=10, choices=[("M", "Homme"), ("F", "Femme")], verbose_name="Sexe")

    lieu_naissance = models.CharField(max_length=50, verbose_name="Lieu de naissance")
    date_naissance = models.DateField(verbose_name="Date de naissance")

    etat_civil = models.CharField(max_length=20, choices=[("Célibataire", "Célibataire"), ("Marié", "Marié(e)"), ("Veuf", "Veuf(ve)"), ("Divorcé", "Divorcé(e)")], verbose_name="Etat civil")
    type_carte_identite = models.CharField(max_length=20, choices=TYPES_CARTE_IDENTITE, verbose_name="Type de carte d'identité")
    # models.ForeignKey(TypesCarteIdentite, on_delete=models.CASCADE, verbose_name="")
    num_carte_identite = models.CharField(max_length=50, verbose_name="Numéro de carte d'identité")
    carte_identite_copy = models.ImageField(upload_to="cartes_identite/", verbose_name="Copie de la carte d'identité")
    photo_passport = models.ImageField(upload_to="photos_passport/", verbose_name="Photo de passeport")
    
    province_residence = models.CharField(max_length=20, verbose_name="Province de résidence")
    # models.ForeignKey(Provinces, on_delete=models.CASCADE, verbose_name="")
    ville_residence =models.CharField(max_length=20, verbose_name="Ville de résidence")
    # models.ForeignKey(Villes, on_delete=models.CASCADE, verbose_name="")
    quartier_residence = models.CharField(max_length=20, verbose_name="Quartier de résidence")
    # models.ForeignKey(Quartiers, on_delete=models.CASCADE, verbose_name="")
    avenue_residence = models.CharField(max_length=20, verbose_name="Avenue de résidence")
    # models.ForeignKey(Avenues, on_delete=models.CASCADE, verbose_name="")
    numero_telephone = models.CharField(max_length=20, unique=True, validators=[RegexValidator(regex=r'^0\d{9}$', message="Numéro de téléphone invalide.")], verbose_name="Numéro de téléphone")
    
    reference_code = models.OneToOneField(CodesReference, on_delete=models.CASCADE, max_length=20, unique=True, verbose_name="Code de référence", blank=True, null=True)
    # access_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="Code d'accès")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    status = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom}"
    
    class Meta:
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")

class NumerosAgent(models.Model):
    numero = models.CharField(max_length=20, unique=True, validators=[RegexValidator(regex=r'^0\d{9}$', message="Numéro de téléphone invalide.")], verbose_name="Numéro Agent")
    reseau = models.CharField(max_length=10, choices=[("Airtel", "Airtel"), ("Orange", "Orange"), ("Vodacom", "Vodacom"), ("Africel", "Africel")], verbose_name="Opérateur Réeseau")
    agent = models.ForeignKey(Agents, on_delete=models.CASCADE, verbose_name="Agent")
    description = models.TextField(max_length=255, blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return f"{self.numero} - {self.reseau} de {self.agent}"
    
    class Meta:
        verbose_name = _("Numéro Agent")
        verbose_name_plural = _("Numéros Agent")
