from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from enum import Enum

TYPES_CARTE_IDENTITE = [
    ("CNI", "Carte Nationale d'Identité"),
    ("Passeport", "Passeport"),
    ("Permis de conduire", "Permis de conduire"),
    ("Autre", "Autre"),
]

# Définition des types d'utilisateurs
class TypesUtilisateur(Enum):
    ADMIN = 'administrateur'
    AGENT = 'agent'
    MEMBRE = 'membre'
    ORGANISATION = 'organisation'

# Définition du modèle commun des utilisateurs
class Users(AbstractUser, PermissionsMixin):
    type = models.CharField(max_length=20, choices=[(tag.value, tag.name) for tag in TypesUtilisateur], default=TypesUtilisateur.MEMBRE.value, verbose_name="Type d'utilisateur")

    def is_admin(self):
        return self.type == TypesUtilisateur.ADMIN.value

    def is_agent(self):
        return self.type == TypesUtilisateur.AGENT.value

    def is_membre(self):
        return self.type == TypesUtilisateur.MEMBRE.value

    def is_organisation(self):
        return self.type == TypesUtilisateur.ORGANISATION.value
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

class Provinces(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")

class Villes(models.Model):
    province = models.ForeignKey(Provinces, on_delete=models.CASCADE)
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False

class Quartiers(models.Model):
    ville = models.ForeignKey(Villes, on_delete=models.CASCADE)
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False

class Avenues(models.Model):
    quartier = models.ForeignKey(Quartiers, on_delete=models.CASCADE)
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Avenue")
        verbose_name_plural = _("Avenues")

class EtatsCivil(models.Model):
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = verbose_name = "États civils"
        verbose_name_plural = _("États civils")

class TypesCarteIdentite(models.Model):
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        abstract = False

class NumerosCompte(models.Model):
    numero = models.CharField(max_length=15, unique=True, validators=[RegexValidator(regex=r'^MW-\d{4}-\d{4}-\d{2}$', message="Numéro de compte invalide.")], verbose_name="Numéro de compte")
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')], verbose_name="Devise")
    type = models.CharField(max_length=20, choices=[(tag.value, tag.name) for tag in TypesUtilisateur], default='membre', verbose_name="Type d'utilisateur")

    description = models.TextField(blank=True, null=True, verbose_name="Description")
            

    def __str__(self):
        return self.numero
    
    class Meta:
        verbose_name = "Numéro de compte"
        verbose_name_plural = "Numéros de Compte"

class CodesReference(models.Model):
    code = models.CharField(max_length=10, unique=True, validators=[RegexValidator(regex=r'^RMW-\d{6}$', message="Code de référence invalide.")], verbose_name="Code de référence")
    type = models.CharField(max_length=20, choices=[(tag.value, tag.name) for tag in TypesUtilisateur], default=TypesUtilisateur.MEMBRE.value, verbose_name="Type d'utilisateur")
    description = models.TextField(max_length=255, blank=True, null=True, verbose_name="Description")

    # self.code = f"RMW-{str(randint(1, 999999)).ljust(6, '0')}"

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Code de référence"
        verbose_name_plural = "Codes de référence"

class ContributionsMensuelles(models.Model):
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')], verbose_name="Devise")
    description = models.TextField(max_length=255, blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return f"{self.montant} {self.devise}"

    class Meta:
        verbose_name = "Contribution mensuelle"
        verbose_name_plural = "Contributions mensuelles"

# Définition du modèle d'administrateur
class Administrateurs(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin", primary_key=True)
    
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
    photo_profil = models.ImageField(upload_to="photos_profil/", blank=True, null=True, verbose_name="Photo de profil")

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
    # invitation_code = models.CharField(max_length=20, verbose_name="Code d'invitation")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    # access_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="Code d'accès")
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom}"

    class Meta:
        verbose_name = _("Administrateur")
        verbose_name_plural = _("Administrateurs")
