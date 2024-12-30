from django.contrib import admin
from .models import Transactions, Contributions, Retraits, DepotsObjectif, Transferts, Prêts, TypesPrêt, Fidelites, DepotsInscription, Benefices

admin.site.register(Transactions)
admin.site.register(Contributions)
admin.site.register(Retraits)
admin.site.register(DepotsObjectif)
admin.site.register(DepotsInscription)
admin.site.register(Transferts)
admin.site.register(Prêts)
admin.site.register(TypesPrêt)
admin.site.register(Fidelites)
admin.site.register(Benefices)
