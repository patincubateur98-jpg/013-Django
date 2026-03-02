from django.urls import path

from .views import home

app_name = 'academics'

urlpatterns = [
    path('', home, name='home'),
]
