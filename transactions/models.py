from django.db import models
from membres.models import Membres
from organisations.models import Organisations
from agents.models import Agents
from objectifs.models import Objectifs
from administrateurs.models import Users, Administrateurs
from agents.models import Agents, NumerosAgent

# Définition des constantes

DEVISE_CHOICES = [
    ('USD', 'USD'),
    ('CDF', 'CDF'),
]

STATUS_CHOICES = [
    ('En attente', 'En attente'),
    ('Approuvé', 'Approuvé'),
    ('Rejeté', 'Rejeté'),
    ('Remboursé', 'Remboursé'),
    ('Annulé', 'Annulé')
]

OPERATEURS = [
    ('membre', 'membre'),
    ('organisation', 'organisation')
]

TRANSACTION_CHOICES = [
    ('retrait', 'Retrait'),
    ('retrait_tout', 'Retrait tout'),
    ('retrait_admin', 'Retrait admin'),
    ('retrait_objectif', 'Retrait objectif'),
    ('annulation_objectif', 'Annulation objectif'),
    ('transfert', 'Transfert'),
    ('depot_objectif', 'Dépôt objectif'),
    ('depot_inscription', 'Dépôt inscription'),
    ('contribution', 'Contribution'),
    ('pret', 'Prêt'),
    ('remboursement_pret', 'Remboursement pret')
]

# Définition du modèle de transaction
class Transactions(models.Model):
    operateur = models.CharField(max_length=20, choices=OPERATEURS, default="membre", verbose_name="Opérateur")
    admin = models.ForeignKey(Administrateurs, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Administrateurs")
    membre = models.ForeignKey(Membres, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Membres")
    organisation = models.ForeignKey(Organisations, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Organisations")
    
    agent = models.ForeignKey(Agents, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Agents")
    numero_agent = models.ForeignKey(NumerosAgent, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Numéro de l'agent")
    
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    preuve = models.ImageField(upload_to="preuves/transactions/", blank=True, null=True, verbose_name="Preuve de transaction")
    
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")

    description = models.TextField(blank=True, null=True, verbose_name="Description")
    type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES, verbose_name="Type de transaction")

    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Demande", verbose_name="Statut")

    def __str__(self):
        return f"Transaction de {self.montant} {self.devise} - {self.type} - {self.date}"
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

class BalanceAdmin(models.Model):
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du bénéfice")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    type = models.CharField(max_length=20, choices=[('pret', 'Pret'), ('depot_inscription', 'Dépôt inscription'), ('retrait', 'Retrait'), ('retrait_tout', 'Retrait tout'), ('annulation_objectif', 'Annulation objectif'), ('remboursement_pret', 'Remboursement pret')], verbose_name="Type de balance")
    statut = models.BooleanField(default=True, verbose_name="Statut")
    
    def __str__(self):
        return f"Balance Admin de {self.montant} - {self.date}"

    class Meta:
        verbose_name = "Balance Admin"
        verbose_name_plural = "Balance Admin"

class RetraitsAdmin(models.Model):
    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")

    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="retrait_admin", verbose_name="Transaction")

    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")

    def __str__(self):
        return f"Retrait Admin de {self.montant} - {self.date}"

    class Meta:
        verbose_name = "Retraits Admin"
        verbose_name_plural = "Retraits Admin"

# Modèle pour les types de pret
class TypesPret(models.Model):
    nom = models.CharField(max_length=45, verbose_name="Nom du type de pret")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taux d'intérêt (%)")
    delai_remboursement = models.IntegerField(verbose_name="Delai de remboursement")

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Type de pret"
        verbose_name_plural = "Types de prets"

# Modèle pour les prets
class Prets(models.Model):
    administrateur = models.ForeignKey(Administrateurs, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Administrateur")
    membre = models.ForeignKey(Membres, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Membres")

    type_pret = models.ForeignKey(TypesPret, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Type de pret")
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True, related_name="pret", verbose_name="Transaction")

    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du pret")
    montant_remboursé = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant remboursé")
    solde_remboursé = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Solde remboursé")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date_demande = models.DateTimeField(auto_now_add=True, verbose_name="Date de demande")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    date_remboursement = models.DateTimeField(verbose_name="Date de remboursement")

    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Remboursé", "Remboursé"), ("Depassé", "Depassé"), ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")

    def __str__(self):
        return f"Prêt de {self.montant} {self.devise} - {self.statut}"
    
    class Meta:
        verbose_name = "Prêt"
        verbose_name_plural = "Prêts"

class RemboursementsPret(models.Model):
    pret = models.ForeignKey(Prets, on_delete=models.CASCADE, verbose_name="Pret")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du remboursement")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date de remboursement")
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True, related_name="remboursement_pret", verbose_name="Transaction")
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")

    def __str__(self):
        return f"Remboursement de pret de {self.montant} {self.devise} - {self.date}"

    class Meta:
        verbose_name = "Remboursement de pret"
        verbose_name_plural = "Remboursements de prets"

class Benefices(models.Model):
    pret = models.ForeignKey(Prets, on_delete=models.CASCADE, verbose_name="Prêt")
    membre = models.ForeignKey(Membres, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Membre")
    
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du bénéfice")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date du bénéfice")
    statut = models.BooleanField(default=True, verbose_name="Statut")

# Définition du modèle de contribution
class Contributions(models.Model):
    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    mois = models.DateField(blank=True,null=True,verbose_name="Mois")
    
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="contribution", verbose_name="Transaction")

    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")

    def __str__(self):
        return f"Contribution de {self.montant} - {self.date}"
    
    class Meta:
        verbose_name = "Contribution"
        verbose_name_plural = "Contributions"

class DepotsObjectif(models.Model):
    objectif = models.ForeignKey(Objectifs, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Objectifs")
    
    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="depot_objectif", verbose_name="Transaction")
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")


    def __str__(self):
        return f"Dépôt objectif de {self.montant} - {self.date}"

    class Meta:
        verbose_name = "Dépôt objectif"
        verbose_name_plural = "Dépôts objectifs"

class RetraitsObjectif(models.Model):
    membre = models.ForeignKey(Membres, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Membres")
    objectif = models.ForeignKey(Objectifs, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Objectifs")
    
    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")
    frais = models.FloatField(verbose_name="Frais")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="retrait_objectif", verbose_name="Transaction")
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")


    def __str__(self):
        return f"Retrait objectif de {self.montant} - {self.date}"

    class Meta:
        verbose_name = "Retrait objectif"
        verbose_name_plural = "Retraits objectifs"

class AnnulationObjectif(models.Model):
    membre = models.ForeignKey(Membres, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Membres")
    objectif = models.ForeignKey(Objectifs, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Objectifs")
    
    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")
    frais = models.FloatField(verbose_name="Frais")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="annulation_objectif", verbose_name="Transaction")
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")

    def __str__(self):
        return f"Annulation de l'objectif de {self.montant} {self.devise} - {self.date}"

    class Meta:
        verbose_name = "Annulation objectif"
        verbose_name_plural = "Annulations objectifs"

class Retraits(models.Model):
    membre = models.ForeignKey(Membres, on_delete=models.CASCADE, verbose_name="Membres")
    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")
    frais = models.FloatField(verbose_name="Frais")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")

    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="retrait", verbose_name="Transaction")

    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")



    def __str__(self):
        return f"Retrait de {self.montant} - {self.date}"

    class Meta:
        verbose_name = "Retraits"
        verbose_name_plural = "Retraits"

class DepotsInscription(models.Model):
    membre = models.ForeignKey(Membres, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Membres")

    montant = models.FloatField(verbose_name="Montant", default=10)
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default="USD", verbose_name="Devise")
    preuve= models.ImageField(upload_to="preuves/depots_inscriptions/", blank=True, verbose_name="Preuve de depot")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")

    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True, related_name="depot_inscription", verbose_name="Transaction")
    
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    statut = models.CharField(max_length=20, choices=(("En attente", "En attente"), ("Approuvé", "Approuvé"), ("Rejeté", "Rejeté"),  ("Annulé", "Annulé")), default="En attente", verbose_name="Statut")

    def __str__(self):
        return f"Dépôt inscription de {self.montant} - {self.date}"

    class Meta:
        verbose_name = "Dépôt inscription"
        verbose_name_plural = "Dépôts inscriptions"

class Transferts(models.Model):
    membre_expediteur = models.ForeignKey(Membres, related_name="membres_expediteurs", blank=True, null=True, on_delete=models.CASCADE, verbose_name="Membres")
    membre_destinataire = models.ForeignKey(Membres, related_name= "membres_destinataires", blank=True, null=True, on_delete=models.CASCADE, verbose_name="Membres")
    organisation_expeditrice = models.ForeignKey(Organisations, related_name= "organisations_expeditrices", blank=True, null=True, on_delete=models.CASCADE, verbose_name="Organisation")
    organisation_destinataire = models.ForeignKey(Organisations, related_name="organisations_destinataires", blank=True, null=True, on_delete=models.CASCADE, verbose_name="Organisation")

    montant = models.FloatField(verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, verbose_name="Devise")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    date_approbation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, related_name="transfert", verbose_name="Transaction")

    expediteur = models.CharField(max_length=20, choices=OPERATEURS, verbose_name="Opérateur")
    destinataire = models.CharField(max_length=20, choices=OPERATEURS, verbose_name="Opérateur")

    motif = models.TextField(verbose_name="Motif")
    description = models.TextField(blank=True, null=True, verbose_name="Description")


    def __str__(self):
        return f"Transfert de {self.montant} - {self.date}"
    
    class Meta:
        verbose_name = "Transferts"
        verbose_name_plural = "Transferts"

class Notifications(models.Model):
    titre = models.CharField(max_length=255)
    message = models.TextField()

    type_notification = models.CharField(max_length=50, choices=TRANSACTION_CHOICES+[(None, None)], default=None, verbose_name= "Type de notification")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    lu = models.BooleanField(default=False, verbose_name="Confirmation de lecture")
    utilisateur = models.ForeignKey(Users, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, blank=True, null=True, related_name="notification", verbose_name="Transaction")

    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return self.titre

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

class Fidelites(models.Model):
    membre = models.ForeignKey(Membres, on_delete=models.CASCADE, verbose_name="membre")
    point = models.IntegerField(verbose_name="Point de fidélité")
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, verbose_name="Transaction")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return f"{self.membre} - {self.point} - {self.transaction}"
    
    class Meta:
        verbose_name = "Fidélité"
        verbose_name_plural = "Fidélités"
