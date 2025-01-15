from django.contrib import admin
from .models import Objectifs, TypesObjectif

# barre de rechrche pour les objectifs admin.site.register(Objectifs)
@admin.register(Objectifs)
class ObjectifsAdmin(admin.ModelAdmin):
    search_fields = ("nom", "type__name", "membre__nom", "organisation__nom")
    list_filter = ("statut", "date_creation", "type")
    date_hierarchy = "date_creation"
    ordering = ("-date_creation",)


admin.site.register(TypesObjectif)

