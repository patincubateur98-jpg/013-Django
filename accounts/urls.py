from django.contrib.auth import views as auth_views
from django.urls import path

from .views import acces_refuse, deconnexion

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', deconnexion, name='logout'),
    path('acces-refuse/', acces_refuse, name='acces_refuse'),
]
