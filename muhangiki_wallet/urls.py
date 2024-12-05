from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from . import views
from django.conf.urls.static import static

app_name = "muhangiki_wallet"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin/", admin.site.urls, name="admin"),
    path("agents/", include("agents.urls")),
    path("membres/", include("membres.urls")),
    path("organisations/", include("organisations.urls")),
    path("administrateurs/", include("administrateurs.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if __name__ == "__main__" and True:
    from administrateurs.models import Administrateurs, Users


    if len(Administrateurs.objects.all()) == 0:
        Administrateurs.objects.create(
            nom="Kakule", postnom="Sikahimbula", prenom="Rock",
            sexe="M", lieu_naissance="Goma", date_naissance="1999-1-1",
            etat_civil="Marié", type_carte_identite="CNI", num_carte_identite="AD1234567890",
            province_residence="Nord-Kivu", ville_residence="Goma", quartier_residence="Kyeshero",
            avenue_residence="Douglas", numero_telephone="0909999999", photo_passport="images/default.jpg",
            carte_identite_copy="images/default.jpg",
            user=Users.objects.create_user(
                username="0909999999",
                email="kakule@gmail.com",
                password="1234",
                first_name="Kakule",
                last_name="Rock",
                type="administrateur",
                is_staff=True,
                is_superuser=True
            
            )
        )