from django.db import models
from django.conf import settings
from administrateurs.models import Provinces, Villes, Communes, Quartiers, Avenues, TypesCarteIdentite, NumerosCompte, CodesReference, ContributionsMensuelles, TYPES_CARTE_IDENTITE
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

# Définition du modèle de membre
class Membres(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membre", primary_key=True)

    nom = models.CharField(max_length=20, verbose_name="Nom")
    postnom = models.CharField(max_length=20, verbose_name="Postnom")
    prenom = models.CharField(max_length=20, blank=True, null=True, verbose_name="Prénom")
    
    sexe = models.CharField(max_length=10,null=True,blank=True, choices=[("M", "Homme"), ("F", "Femme")], verbose_name="Sexe")

    lieu_naissance = models.CharField(max_length=50, null=True,blank=True, verbose_name="Lieu de naissance")
    date_naissance = models.DateField(null=True,blank=True,verbose_name="Date de naissance")

    etat_civil = models.CharField(max_length=20, null=True,blank=True, choices=[("Célibataire", "Célibataire"), ("Marié", "Marié(e)"), ("Veuf", "Veuf(ve)"), ("Divorcé", "Divorcé(e)")], verbose_name="Etat civil")
    type_carte_identite = models.CharField(null=True,blank=True, max_length=20, choices=TYPES_CARTE_IDENTITE, verbose_name="Type de carte d'identité")
    # models.ForeignKey(TypesCarteIdentite, on_delete=models.CASCADE, verbose_name="")
    num_carte_identite = models.CharField(null=True,blank=True,max_length=50, verbose_name="Numéro de carte d'identité")
    carte_identite_copy = models.ImageField(upload_to="identite/", verbose_name="Copie de la carte d'identité")
    photo_profile = models.ImageField(null=True,blank=True,upload_to="profile/", verbose_name="Photo de profile")

    province_residence = models.ForeignKey(Provinces,null=True,blank=True, on_delete=models.CASCADE, verbose_name="Province de résidence")
    ville_residence = models.ForeignKey(Villes, null=True,blank=True, on_delete=models.CASCADE, verbose_name="Ville de résidence")
    commune_residence = models.ForeignKey(Communes, null=True,blank=True, on_delete=models.CASCADE, verbose_name="Commune de résidence")
    quartier_residence = models.ForeignKey(Quartiers,null=True,blank=True, on_delete=models.CASCADE, verbose_name="Quartier de résidence")
    avenue_residence = models.ForeignKey(Avenues, null=True,blank=True, on_delete=models.CASCADE, verbose_name="Avenue de résidence")
    numero_residence = models.IntegerField(null=True,blank=True, verbose_name="Numéro de résidence")
    
    numero_telephone = models.CharField(max_length=20,unique=True,validators=[RegexValidator(regex=r'^243\d{9}$', message="Le numéro de téléphone doit commencer par '243' et être suivi de 9 chiffres (ex: 243992131675).")],verbose_name="Numéro de téléphone")
    
    reference_code = models.OneToOneField(CodesReference, on_delete=models.CASCADE, max_length=20, unique=True, verbose_name="Code de référence", blank=True, null=True)
    invitation_code = models.CharField(null=True, blank=True, max_length=20, verbose_name="Code d'invitation")
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    compte_CDF = models.OneToOneField(NumerosCompte, on_delete=models.CASCADE, max_length=15, unique=True, related_name="membre", verbose_name="Compte CDF")
    compte_USD = models.OneToOneField(NumerosCompte, on_delete=models.CASCADE, max_length=15, unique=True, verbose_name="Compte USD")

    contribution_mensuelle = models.ForeignKey(ContributionsMensuelles,null=True,blank=True, on_delete=models.CASCADE, verbose_name="Contribution mensuelle")
    mois_contribution = models.DateField(null=True,blank=True,auto_now_add=True, verbose_name="Mois de contribution")

    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nom} {self.postnom} {self.prenom}"
    class Meta:
        verbose_name = _("Membre")
        verbose_name_plural = _("Membres")


class Registre(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_agent = models.TextField(verbose_name="User agent")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.date}"

    class Meta:
        verbose_name = _("Registre")
        verbose_name_plural = _("Registres")
