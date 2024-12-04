from django.db import models
from membres.models import Membres
from organisations.models import Organisations

# Définition du modèle de type d'objectif
class TypesObjectif(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom du type d'objectif")
    description = models.TextField(verbose_name="Description", blank=True, null=True)

    def __str__(self):
        return self.name

# Définition du modèle d'objectif
class Objectifs(models.Model):
    membre = models.ForeignKey(Membres, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Client")
    organisation = models.ForeignKey(Organisations, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Organisations")
    operateur = models.CharField(max_length=20, choices=(("membre", "membre"), ("organisation", "organisation")), verbose_name="Opérateur")

    montant = models.FloatField(verbose_name="Montant", default=0)
    montant_cible = models.FloatField(verbose_name="Montant cible")
    devise = models.CharField(max_length=10, choices=(("CDF", "CDF"), ("USD", "USD")), verbose_name="Devise")

    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin", blank=True, null=True)
    date_creation = models.DateField(auto_now_add=True, verbose_name="Date de création")

    nom = models.CharField(max_length=255, verbose_name="Nom de l'objectif")
    type = models.ForeignKey(TypesObjectif, on_delete=models.CASCADE, verbose_name="Type d'objectif", blank=True, null=True)

    description = models.TextField(verbose_name="Description", blank=True, null=True)
    statut = models.CharField(max_length=20, choices=(("En cours", "En cours"), ("Atteint", "Atteint"), ("Epuisé", "Epuisé"), ("Annulé", "Annulé")), default="En cours", verbose_name="Statut")

    def pourcentage_atteint(self):
        return (self.montant / self.montant_cible) * 100


    def __str__(self):
        return f"Objectif de {self.montant_cible} {self.devise} pour {self.type} de {self.membre} " if self.membre else f"Objectif de {self.organisation} "
