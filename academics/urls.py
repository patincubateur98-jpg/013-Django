from django.urls import path

from .views import (
    calendrier_classe,
    calendriers_classes,
    detail_classe,
    detail_cours,
    detail_etudiant,
    detail_presence,
    detail_tuteur,
    home,
    saisie_presences_cours,
    vue_presences_cours,
    liste_classes,
    liste_cours,
    liste_etudiants,
    liste_presences,
    liste_tuteurs,
    synthese_tuteurs_par_classe,
)

app_name = 'academics'

urlpatterns = [
    path('', home, name='home'),
    path('calendriers/classes/', calendriers_classes, name='calendriers_classes'),
    path('calendriers/classes/<int:classe_id>/', calendrier_classe, name='calendrier_classe'),
    path('presences/saisie/', saisie_presences_cours, name='saisie_presences_cours'),
    path('presences/vue/', vue_presences_cours, name='vue_presences_cours'),
    path('etudiants/', liste_etudiants, name='liste_etudiants'),
    path('etudiants/<int:etudiant_id>/', detail_etudiant, name='detail_etudiant'),
    path('cours/', liste_cours, name='liste_cours'),
    path('cours/<int:cours_id>/', detail_cours, name='detail_cours'),
    path('presences/', liste_presences, name='liste_presences'),
    path('presences/<int:presence_id>/', detail_presence, name='detail_presence'),
    path('tuteurs/', liste_tuteurs, name='liste_tuteurs'),
    path('tuteurs/synthese/', synthese_tuteurs_par_classe, name='synthese_tuteurs_par_classe'),
    path('tuteurs/<int:tuteur_id>/', detail_tuteur, name='detail_tuteur'),
    path('classes/', liste_classes, name='liste_classes'),
    path('classes/<int:classe_id>/', detail_classe, name='detail_classe'),
]
