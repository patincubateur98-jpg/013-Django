from datetime import timedelta
import random

from django.core.management.base import BaseCommand
from django.db.models import Count, Min
from django.utils import timezone

from academics.models import Cours, Etudiant, Presence, PresenceEtudiant


NOMBRE_COLONNES_PAR_COURS = {
    '001': 5,
    '101': 9,
    '201': 9,
    '301': 9,
}


def normaliser_code(code):
    brut = (code or '').strip()
    if brut in NOMBRE_COLONNES_PAR_COURS:
        return brut
    chiffres = ''.join(ch for ch in brut if ch.isdigit())
    if len(chiffres) >= 3:
        return chiffres[-3:]
    return brut


def nombre_colonnes(cours):
    return NOMBRE_COLONNES_PAR_COURS.get(normaliser_code(cours.code), 5)


def date_debut_par_classe(classe_id):
    premiere = Presence.objects.filter(classe_id=classe_id).aggregate(min_date=Min('date'))['min_date']
    if premiere:
        return premiere
    return timezone.localdate() - timedelta(days=30)


class Command(BaseCommand):
    help = "Génère aléatoirement les statuts de présence (P/A/AE) pour les classes/cours existants."

    def add_arguments(self, parser):
        parser.add_argument('--seed', type=int, default=42, help='Graine aléatoire pour résultats reproductibles.')
        parser.add_argument('--overwrite', action='store_true', help='Écrase les statuts déjà présents.')
        parser.add_argument('--present-weight', type=float, default=0.78, help='Probabilité de statut P.')
        parser.add_argument('--absent-weight', type=float, default=0.17, help='Probabilité de statut A.')
        parser.add_argument('--excused-weight', type=float, default=0.05, help='Probabilité de statut AE.')

    def handle(self, *args, **options):
        rng = random.Random(options['seed'])
        overwrite = options['overwrite']

        weights = [
            options['present_weight'],
            options['absent_weight'],
            options['excused_weight'],
        ]
        total_weight = sum(weights)
        if total_weight <= 0:
            self.stdout.write(self.style.ERROR('Les probabilités doivent être strictement positives.'))
            return
        weights = [w / total_weight for w in weights]

        combinaisons = list(
            Etudiant.objects.values('classe_id', 'cours_id')
            .annotate(n=Count('id'))
            .order_by('classe_id', 'cours_id')
        )

        if not combinaisons:
            self.stdout.write(self.style.WARNING('Aucune combinaison classe/cours avec étudiants.'))
            return

        total_presences = 0
        total_statuts = 0
        total_combinaisons = 0

        for combo in combinaisons:
            classe_id = combo['classe_id']
            cours_id = combo['cours_id']

            cours = Cours.objects.get(id=cours_id)
            n_col = nombre_colonnes(cours)
            debut = date_debut_par_classe(classe_id)

            dates_existantes = list(
                Presence.objects.filter(classe_id=classe_id, cours_id=cours_id)
                .order_by('date')
                .values_list('date', flat=True)[:n_col]
            )

            dates = list(dates_existantes)
            while len(dates) < n_col:
                dates.append(debut + timedelta(days=7 * len(dates)))

            for d in dates:
                Presence.objects.get_or_create(date=d, classe_id=classe_id, cours_id=cours_id)

            etudiants_ids = list(
                Etudiant.objects.filter(classe_id=classe_id, cours_id=cours_id)
                .order_by('id')
                .values_list('id', flat=True)
            )

            for etudiant_id in etudiants_ids:
                for d in dates:
                    statut_aleatoire = rng.choices(['P', 'A', 'AE'], weights=weights, k=1)[0]
                    if overwrite:
                        PresenceEtudiant.objects.update_or_create(
                            etudiant_id=etudiant_id,
                            date=d,
                            defaults={'statut': statut_aleatoire},
                        )
                        total_statuts += 1
                    else:
                        _, created = PresenceEtudiant.objects.get_or_create(
                            etudiant_id=etudiant_id,
                            date=d,
                            defaults={'statut': statut_aleatoire},
                        )
                        if created:
                            total_statuts += 1

            total_presences += len(dates)
            total_combinaisons += 1

        self.stdout.write(self.style.SUCCESS('Génération aléatoire terminée.'))
        self.stdout.write(
            f"Combinaisons traitées: {total_combinaisons} | Dates présence assurées: {total_presences} | Statuts créés/mis à jour: {total_statuts}"
        )