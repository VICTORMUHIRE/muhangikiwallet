from django.contrib import admin
from .models import Administrateurs, Users
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Provinces, Villes, Quartiers, Avenues, EtatsCivil, TypesCarteIdentite, ContributionsMensuelles, CodesReference, NumerosCompte

# Register your models here.
class UserAdmin(BaseUserAdmin):
    list_display = ('first_name', 'last_name', 'email', 'username', 'type')
    list_filter = ('type',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (('Type'), {'fields': ('type',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'type')}
         ),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)


admin.site.register(Users, UserAdmin)
admin.site.register(Administrateurs)

# admin.site.register(Provinces)
# admin.site.register(Villes)
# admin.site.register(Quartiers)
# admin.site.register(Avenues)
# admin.site.register(EtatsCivil)
# admin.site.register(TypesCarteIdentite)

admin.site.register(ContributionsMensuelles)
admin.site.register(CodesReference)
admin.site.register(NumerosCompte)
