from django.urls import path

from .views import historique

app_name = 'journal'

urlpatterns = [
	path('', historique, name='historique'),
]
