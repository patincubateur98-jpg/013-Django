"""
Configuration des URL pour le projet config.

La liste `urlpatterns` associe les URL aux vues. Pour plus d'informations, voir :
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Exemples :
Vues fonctionnelles
    1. Ajouter un import :  from my_app import views
    2. Ajouter une URL à urlpatterns :  path('', views.home, name='home')
Vues basées sur des classes
    1. Ajouter un import :  from other_app.views import Home
    2. Ajouter une URL à urlpatterns :  path('', Home.as_view(), name='home')
Inclure un autre fichier URLconf
    1. Importer la fonction include() : from django.urls import include, path
    2. Ajouter une URL à urlpatterns :  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('', include('academics.urls')),
    path('journal/', include('journal.urls')),
    path('admin/', admin.site.urls),
]
