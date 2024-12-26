from django.contrib import admin
from .models import Transactions, Contributions, Retraits, DepotsObjectif, Transferts, Prets, TypesPret, Fidelites, DepotsInscription, Benefices, RemboursementsPret, RetraitsObjectif, AnnulationObjectif, RetraitsAdmin, BalanceAdmin

admin.site.register(Transactions)
admin.site.register(Contributions)
admin.site.register(Retraits)
admin.site.register(RetraitsObjectif)
admin.site.register(RetraitsAdmin)
admin.site.register(AnnulationObjectif)
admin.site.register(RemboursementsPret)
admin.site.register(BalanceAdmin)
admin.site.register(DepotsObjectif)
admin.site.register(DepotsInscription)
admin.site.register(Prets)
admin.site.register(TypesPret)
admin.site.register(Benefices)
