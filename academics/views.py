from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Min
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import role_required

from .models import Classe, Cours, Etudiant, Presence, PresenceEtudiant, Tuteur


NOMBRE_COLONNES_PAR_COURS = {
	'001': 5,
	'101': 9,
	'201': 9,
	'301': 9,
}

DELAI_JOURS_ENTRE_COURS = 14
PAS_JOURS_PAR_COLONNE = 7

DECALAGE_JOURS_PAR_COURS = {
	'001': 0,
	'101': DELAI_JOURS_ENTRE_COURS,
	'201': 2 * DELAI_JOURS_ENTRE_COURS,
}

COURS_PRECEDENT = {
	'101': '001',
	'201': '101',
	'301': '201',
}


def _normaliser_code_cours(code):
	code_brut = (code or '').strip()
	if code_brut in NOMBRE_COLONNES_PAR_COURS:
		return code_brut

	chiffres = ''.join(ch for ch in code_brut if ch.isdigit())
	if len(chiffres) >= 3:
		return chiffres[-3:]

	return code_brut


def _libelle_cours_calendrier(code):
	code_brut = (code or '').strip()
	if not code_brut:
		return '-'
	if ' ' in code_brut:
		return code_brut.split()[0]
	return code_brut


def _nombre_colonnes(cours):
	code = _normaliser_code_cours(cours.code)
	if code in NOMBRE_COLONNES_PAR_COURS:
		return NOMBRE_COLONNES_PAR_COURS[code]

	return 5


def _date_debut_reference_classe(classe):
	"""Calcule la date de début de référence (cours 001) pour une classe.

	Règles:
	- Si on a déjà des présences 001/101/201 pour la classe, on déduit le début 001.
	- Sinon, démarrage par défaut à un mois en arrière pour cohérence.
	"""
	presences = Presence.objects.select_related('cours').filter(classe_id=classe.id).order_by('date')
	min_date_par_code = {}

	for presence in presences:
		code = _normaliser_code_cours(presence.cours.code)
		if code in {'001', '101', '201'} and code not in min_date_par_code:
			min_date_par_code[code] = presence.date

	if '001' in min_date_par_code:
		return min_date_par_code['001']
	if '101' in min_date_par_code:
		return min_date_par_code['101'] - timedelta(days=DELAI_JOURS_ENTRE_COURS)
	if '201' in min_date_par_code:
		return min_date_par_code['201'] - timedelta(days=2 * DELAI_JOURS_ENTRE_COURS)

	return timezone.localdate() - timedelta(days=30)


def _dates_suggerees(classe, cours, nombre_colonnes):
	debut_reference = _date_debut_reference_classe(classe)
	code = _normaliser_code_cours(cours.code)
	decalage = DECALAGE_JOURS_PAR_COURS.get(code, 0)
	debut_cours = debut_reference + timedelta(days=decalage)

	return [
		str(debut_cours + timedelta(days=PAS_JOURS_PAR_COLONNE * idx))
		for idx in range(nombre_colonnes)
	]


def _get_cours_by_code_normalise(code_normalise):
	for cours in Cours.objects.all():
		if _normaliser_code_cours(cours.code) == code_normalise:
			return cours
	return None


def _initialiser_etudiants_depuis_cours_precedent(classe, cours):
	"""Crée la liste d'étudiants du cours courant à partir du cours précédent si vide."""
	etudiants_courant_qs = Etudiant.objects.filter(classe_id=classe.id, cours_id=cours.id)
	if etudiants_courant_qs.exists():
		return 0

	code_courant = _normaliser_code_cours(cours.code)
	code_precedent = COURS_PRECEDENT.get(code_courant)
	if not code_precedent:
		return 0

	cours_precedent = _get_cours_by_code_normalise(code_precedent)
	if cours_precedent is None:
		return 0

	etudiants_precedent = Etudiant.objects.filter(classe_id=classe.id, cours_id=cours_precedent.id).order_by('nom', 'prenom')
	created = 0

	for etu in etudiants_precedent:
		Etudiant.objects.create(
			genre=etu.genre,
			nom=etu.nom,
			prenom=etu.prenom,
			email=etu.email,
			telephone=etu.telephone,
			presence=etu.presence,
			classe_id=classe.id,
			cours_id=cours.id,
			tuteur_id=etu.tuteur_id,
		)
		created += 1

	return created


def _ctx(active_nav, extra=None):
	base = {'active_nav': active_nav}
	if extra:
		base.update(extra)
	return base


@login_required
def home(request):
	return render(request, 'academics/home.html', _ctx('home'))


@login_required
def liste_etudiants(request):
	etudiants = Etudiant.objects.select_related('classe', 'cours', 'tuteur').all()
	return render(request, 'academics/liste_etudiants.html', _ctx('etudiants', {'etudiants': etudiants}))


@login_required
def liste_classes(request):
	classes = list(
		Classe.objects.annotate(
			nombre_etudiants=Count('etudiants', distinct=True),
			nombre_tuteurs=Count('etudiants__tuteur', distinct=True),
		).order_by('numero', 'nom')
	)

	presences = Presence.objects.select_related('cours').filter(
		classe_id__in=[c.id for c in classes]
	).order_by('date')

	debut_par_classe = {}
	for presence in presences:
		cid = presence.classe_id
		if cid not in debut_par_classe:
			debut_par_classe[cid] = {'001': None, '101': None, '201': None}

		code = _normaliser_code_cours(presence.cours.code)
		if code in {'001', '101', '201'} and debut_par_classe[cid][code] is None:
			debut_par_classe[cid][code] = presence.date

	lignes = []
	for classe in classes:
		debut = debut_par_classe.get(classe.id, {'001': None, '101': None, '201': None})
		lignes.append(
			{
				'classe': classe,
				'nombre_etudiants': classe.nombre_etudiants,
				'nombre_tuteurs': classe.nombre_tuteurs,
				'debut_001': debut['001'],
				'debut_101': debut['101'],
				'debut_201': debut['201'],
			}
		)

	return render(request, 'academics/liste_classes.html', _ctx('classes', {'lignes': lignes}))


@login_required
def detail_classe(request, classe_id):
	# Même rendu que la page calendrier de classe pour uniformiser la navigation.
	return calendrier_classe(request, classe_id)


@login_required
def detail_etudiant(request, etudiant_id):
	etudiant = get_object_or_404(
		Etudiant.objects.select_related('classe', 'cours', 'tuteur'),
		id=etudiant_id,
	)

	cle_nom = (etudiant.nom or '').strip()
	cle_prenom = (etudiant.prenom or '').strip()
	cle_email = (etudiant.email or '').strip()

	ids_equivalents = list(
		Etudiant.objects.filter(
			classe_id=etudiant.classe_id,
			nom__iexact=cle_nom,
			prenom__iexact=cle_prenom,
			email__iexact=cle_email,
		).values_list('id', flat=True)
	)

	if not ids_equivalents:
		ids_equivalents = [etudiant.id]

	presences_qs = PresenceEtudiant.objects.filter(etudiant_id__in=ids_equivalents)
	synthese_presence = {
		'total_p': presences_qs.filter(statut='P').count(),
		'total_ae': presences_qs.filter(statut='AE').count(),
		'total_a': presences_qs.filter(statut='A').count(),
	}

	priorite_statut = {'A': 3, 'AE': 2, 'P': 1}
	historique_map = {}
	for date, statut in presences_qs.values_list('date', 'statut'):
		if statut not in {'P', 'A', 'AE'}:
			continue
		if date not in historique_map:
			historique_map[date] = statut
		else:
			actuel = historique_map[date]
			if priorite_statut.get(statut, 0) > priorite_statut.get(actuel, 0):
				historique_map[date] = statut

	historique_presences = [
		{'date': date, 'statut': statut}
		for date, statut in sorted(historique_map.items(), key=lambda item: item[0], reverse=True)
	]

	return render(
		request,
		'academics/detail_etudiant.html',
		_ctx(
			'etudiants',
			{
				'etudiant': etudiant,
				'synthese_presence': synthese_presence,
				'historique_presences': historique_presences,
			},
		),
	)


@login_required
def liste_tuteurs(request):
	tuteurs = (
		Tuteur.objects.annotate(
			nombre_etudiants=Count('etudiants', distinct=True),
			classe_numero=Min('etudiants__classe__numero'),
			classe_nom=Min('etudiants__classe__nom'),
			cours_code=Min('etudiants__cours__code'),
		)
		.order_by('classe_numero', 'cours_code', 'nom', 'prenom')
	)
	return render(request, 'academics/liste_tuteurs.html', _ctx('tuteurs', {'tuteurs': tuteurs}))


@login_required
def detail_tuteur(request, tuteur_id):
	tuteur = get_object_or_404(Tuteur, id=tuteur_id)
	etudiants = Etudiant.objects.select_related('classe', 'cours').filter(tuteur_id=tuteur.id).order_by('nom', 'prenom')
	return render(request, 'academics/detail_tuteur.html', _ctx('tuteurs', {'tuteur': tuteur, 'etudiants': etudiants}))


@login_required
def synthese_tuteurs_par_classe(request):
	classe_id = request.GET.get('classe_id')

	synthese = list(
		Etudiant.objects.values(
			'classe_id',
			'classe__numero',
			'classe__nom',
		)
		.annotate(
			nombre_tuteurs=Count('tuteur', distinct=True),
			nombre_etudiants=Count('id', distinct=True),
		)
		.order_by('classe__numero', 'classe__nom')
	)

	classe = None
	tuteurs = []
	if classe_id:
		classe = get_object_or_404(Classe, id=classe_id)
		tuteurs = list(
			Tuteur.objects.filter(etudiants__classe_id=classe.id)
			.annotate(
				nombre_etudiants=Count('etudiants', distinct=True),
				cours_code=Min('etudiants__cours__code'),
			)
			.distinct()
			.order_by('cours_code', 'nom', 'prenom')
		)

	return render(
		request,
		'academics/synthese_tuteurs_par_classe.html',
		_ctx('tuteurs_synthese', {'synthese': synthese, 'classe': classe, 'tuteurs': tuteurs}),
	)


@login_required
def liste_cours(request):
	cours = Cours.objects.annotate(nombre_etudiants=Count('etudiants')).order_by('code')
	return render(request, 'academics/liste_cours.html', _ctx('cours', {'cours': cours}))


@login_required
def detail_cours(request, cours_id):
	cours = get_object_or_404(Cours, id=cours_id)
	etudiants = Etudiant.objects.select_related('classe', 'tuteur').filter(cours_id=cours.id).order_by('nom', 'prenom')
	return render(request, 'academics/detail_cours.html', _ctx('cours', {'cours': cours, 'etudiants': etudiants}))


@login_required
def liste_presences(request):
	presences = list(
		Presence.objects.select_related('classe', 'cours').order_by('date', 'classe__numero', 'cours__code')
	)

	toutes_dates = sorted({p.date for p in presences})
	aujourdhui = timezone.localdate()
	dates_courantes = [d for d in toutes_dates if d >= aujourdhui]
	dates_passees = [d for d in toutes_dates if d < aujourdhui]

	# Une ligne par couple (classe, cours) et un lien détail par date.
	rows_map = {}
	for p in presences:
		key = (p.classe_id, p.cours_id)
		if key not in rows_map:
			rows_map[key] = {
				'classe': p.classe,
				'cours': p.cours,
				'cells': {},
			}
		rows_map[key]['cells'][p.date] = p

	rows = sorted(
		rows_map.values(),
		key=lambda r: (r['classe'].numero, (r['classe'].nom or '').lower(), str(r['cours'])),
	)

	for row in rows:
		row['cells_courantes'] = [row['cells'].get(d) for d in dates_courantes]
		row['cells_passees'] = [row['cells'].get(d) for d in dates_passees]

	return render(
		request,
		'academics/liste_presences.html',
		_ctx(
			'presences',
			{
				'rows': rows,
				'dates_courantes': dates_courantes,
				'dates_passees': dates_passees,
			},
		),
	)


@login_required
def detail_presence(request, presence_id):
	presence = get_object_or_404(Presence.objects.select_related('classe', 'cours'), id=presence_id)
	presences_etudiants = PresenceEtudiant.objects.select_related('etudiant').filter(
		date=presence.date,
		etudiant__classe_id=presence.classe_id,
		etudiant__cours_id=presence.cours_id,
	).order_by('etudiant__nom', 'etudiant__prenom')

	total_etudiants = presences_etudiants.count()
	nombre_presents = presences_etudiants.filter(statut='P').count()
	nombre_absents_excuses = presences_etudiants.filter(statut='AE').count()
	nombre_absents = presences_etudiants.filter(statut='A').count()
	absences = presences_etudiants.filter(statut__in=['A', 'AE'])

	return render(
		request,
		'academics/detail_presence.html',
		_ctx(
			'presences',
			{
				'presence': presence,
				'presences_etudiants': presences_etudiants,
				'total_etudiants': total_etudiants,
				'nombre_presents': nombre_presents,
				'nombre_absents_excuses': nombre_absents_excuses,
				'nombre_absents': nombre_absents,
				'absences': absences,
			},
		),
	)


@login_required
def calendriers_classes(request):
	classes = Classe.objects.annotate(
		nombre_dates=Count('presences', distinct=True),
		derniere_date=Max('presences__date'),
	).order_by('numero', 'nom')

	toutes_dates = list(
		Presence.objects.values_list('date', flat=True).distinct().order_by('date')
	)

	presences = Presence.objects.select_related('cours').filter(
		classe_id__in=[c.id for c in classes],
		date__in=toutes_dates,
	).order_by('classe_id', 'date', 'cours__code')

	map_classe_date = defaultdict(dict)
	for presence in presences:
		cle = (presence.classe_id, presence.date)
		code = presence.cours.code
		if code not in map_classe_date[cle]:
			map_classe_date[cle][code] = presence

	lignes = []
	for classe in classes:
		cells = []
		for date in toutes_dates:
			presences_uniques = list(map_classe_date.get((classe.id, date), {}).values())

			liens_map = {}
			for presence in presences_uniques:
				libelle = _libelle_cours_calendrier(presence.cours.code)
				if libelle not in liens_map:
					liens_map[libelle] = presence

			liens = [
				{
					'label': 'Synthèse jour' if libelle == 'PCNC' else libelle,
					'presence_id': presence.id,
				}
				for libelle, presence in sorted(liens_map.items(), key=lambda item: item[0])
			]
			cells.append(
				{
					'date': date,
					'presences': presences_uniques,
					'liens': liens,
				}
			)
		lignes.append({'classe': classe, 'cells': cells})

	return render(
		request,
		'academics/calendriers_classes.html',
		_ctx('calendriers', {'classes': classes, 'dates': toutes_dates, 'lignes': lignes}),
	)


@login_required
def calendrier_classe(request, classe_id):
	classe = get_object_or_404(Classe, id=classe_id)
	dates = list(
		Presence.objects.filter(classe_id=classe.id)
		.values_list('date', flat=True)
		.distinct()
		.order_by('date')
	)

	etudiants = list(
		Etudiant.objects.filter(classe_id=classe.id)
		.select_related('cours', 'tuteur')
		.order_by('nom', 'prenom')
	)

	groupes = {}
	for etudiant in etudiants:
		cle = (
			(etudiant.nom or '').strip().lower(),
			(etudiant.prenom or '').strip().lower(),
			(etudiant.email or '').strip().lower(),
		)
		if cle not in groupes:
			groupes[cle] = {'etudiant': etudiant, 'ids': []}
		groupes[cle]['ids'].append(etudiant.id)

	statuts = PresenceEtudiant.objects.filter(
		etudiant_id__in=[e.id for e in etudiants],
		date__in=dates,
	).values_list('etudiant_id', 'date', 'statut')

	priorite_statut = {'A': 3, 'AE': 2, 'P': 1}
	map_statut_par_id = {}
	for etudiant_id, date, statut in statuts:
		if statut not in {'P', 'A', 'AE'}:
			continue
		map_statut_par_id[(etudiant_id, date)] = statut

	lignes = []
	for groupe in groupes.values():
		etudiant = groupe['etudiant']
		ids = groupe['ids']
		cells = []
		cumul_p = 0
		total_a = 0

		for date in dates:
			statuts_date = [
				map_statut_par_id[(eid, date)]
				for eid in ids
				if (eid, date) in map_statut_par_id
			]
			statut = None
			if statuts_date:
				statut = max(statuts_date, key=lambda s: priorite_statut.get(s, 0))

			if statut in {'P', 'A', 'AE'}:
				if statut == 'P':
					cumul_p += 1
				if statut == 'A':
					total_a += 1
				cells.append({'date': date, 'statut': statut, 'cumul_p': cumul_p})
			else:
				cells.append({'date': date, 'statut': '-', 'cumul_p': '-'})

		if total_a >= 3:
			couleur_nom = '#ff9999'
		elif total_a == 2:
			couleur_nom = '#fff59d'
		else:
			couleur_nom = ''

		lignes.append(
			{
				'etudiant': etudiant,
				'cells': cells,
				'total_a': total_a,
				'couleur_nom': couleur_nom,
			}
		)

	etudiants_affiches = [
		{
			'id': ligne['etudiant'].id,
			'nom': ligne['etudiant'].nom,
			'prenom': ligne['etudiant'].prenom,
			'total_a': ligne['total_a'],
			'couleur_nom': ligne['couleur_nom'],
		}
		for ligne in lignes
	]

	matrice_dates = []
	for idx, date in enumerate(dates):
		cells_date = []
		for ligne in lignes:
			cell = ligne['cells'][idx]
			cells_date.append({'statut': cell['statut'], 'cumul_p': cell['cumul_p']})
		matrice_dates.append({'date': date, 'cells': cells_date})

	return render(
		request,
		'academics/calendrier_classe.html',
		_ctx(
			'calendriers',
			{
				'classe': classe,
				'dates': dates,
				'lignes': lignes,
				'etudiants_affiches': etudiants_affiches,
				'matrice_dates': matrice_dates,
			},
		),
	)


@role_required('ADMIN', 'COORDINATEUR')
def saisie_presences_cours(request):
	classes = Classe.objects.order_by('numero', 'nom')
	cours_liste = Cours.objects.order_by('code')
	combinaisons = list(
		Etudiant.objects.values(
			'classe_id',
			'classe__numero',
			'classe__nom',
			'cours_id',
			'cours__code',
		)
		.annotate(nombre_etudiants=Count('id'))
		.order_by('classe__numero', 'cours__code')
	)

	classe_id = request.GET.get('classe_id') or request.POST.get('classe_id')
	cours_id = request.GET.get('cours_id') or request.POST.get('cours_id')

	classe = None
	cours = None
	etudiants = []
	nombre_colonnes = 0
	dates = []
	colonnes = []
	lignes_saisie = []
	resume_saisie = None
	auto_reprise_count = 0
	message_reprise = None

	if classe_id and cours_id:
		classe = get_object_or_404(Classe, id=classe_id)
		cours = get_object_or_404(Cours, id=cours_id)
		if request.method == 'POST' and request.POST.get('action') == 'reprendre_precedent':
			auto_reprise_count = _initialiser_etudiants_depuis_cours_precedent(classe, cours)
			if auto_reprise_count > 0:
				message_reprise = f"Liste reprise du cours précédent: {auto_reprise_count} étudiant(s)."
			else:
				message_reprise = "Aucune reprise effectuée (liste déjà présente ou cours précédent introuvable)."

		nombre_colonnes = _nombre_colonnes(cours)
		etudiants = list(
			Etudiant.objects.filter(classe_id=classe.id, cours_id=cours.id).order_by('nom', 'prenom')
		)

		dates_existantes = list(
			Presence.objects.filter(classe_id=classe.id, cours_id=cours.id)
			.order_by('date')
			.values_list('date', flat=True)[:nombre_colonnes]
		)
		dates = [str(d) for d in dates_existantes]
		while len(dates) < nombre_colonnes:
			dates.append('')

		dates_proposees = _dates_suggerees(classe, cours, nombre_colonnes)
		for idx in range(nombre_colonnes):
			if not dates[idx]:
				dates[idx] = dates_proposees[idx]

		colonnes = [
			{'index': i, 'date': dates[i - 1] if i - 1 < len(dates) else ''}
			for i in range(1, nombre_colonnes + 1)
		]

		dates_non_vides = [col['date'] for col in colonnes if col['date']]
		statuts_existants = {}
		if dates_non_vides and etudiants:
			lignes_existantes = PresenceEtudiant.objects.filter(
				etudiant_id__in=[e.id for e in etudiants],
				date__in=dates_non_vides,
			)
			for ligne in lignes_existantes:
				statuts_existants[(ligne.etudiant_id, str(ligne.date))] = ligne.statut

		for etudiant in etudiants:
			cells = []
			for col in colonnes:
				statut = ''
				if col['date']:
					statut = statuts_existants.get((etudiant.id, col['date']), '')
				cells.append({'index': col['index'], 'statut': statut})
			lignes_saisie.append({'etudiant': etudiant, 'cells': cells})

		total_lignes_saisies = PresenceEtudiant.objects.filter(
			etudiant_id__in=[e.id for e in etudiants],
			date__in=dates_non_vides,
		).count()

		nombre_dates_saisies = len([d for d in dates_non_vides if d])
		capacite = len(etudiants) * nombre_colonnes if etudiants else 0
		resume_saisie = {
			'nombre_etudiants': len(etudiants),
			'nombre_dates_saisies': nombre_dates_saisies,
			'total_lignes_saisies': total_lignes_saisies,
			'capacite_theorique': capacite,
		}

	if request.method == 'POST' and classe and cours:
		dates_saisies = [request.POST.get(f'date_{i}', '').strip() for i in range(1, nombre_colonnes + 1)]

		for i, date_str in enumerate(dates_saisies, start=1):
			if not date_str:
				continue

			presence = (
				Presence.objects.filter(date=date_str, classe_id=classe.id, cours_id=cours.id)
				.order_by('id')
				.first()
			)
			if presence is None:
				Presence.objects.create(date=date_str, classe_id=classe.id, cours_id=cours.id)

			for etudiant in etudiants:
				statut = request.POST.get(f'statut_{etudiant.id}_{i}', '').strip().upper()
				if statut not in {'P', 'A', 'AE'}:
					continue
				PresenceEtudiant.objects.update_or_create(
					etudiant_id=etudiant.id,
					date=date_str,
					defaults={'statut': statut},
				)

		return redirect(f"/presences/saisie/?classe_id={classe.id}&cours_id={cours.id}&saved=1")

	saved = request.GET.get('saved') == '1'

	return render(
		request,
		'academics/saisie_presences_cours.html',
		_ctx('saisie', {
			'classes': classes,
			'cours_liste': cours_liste,
			'classe': classe,
			'cours': cours,
			'etudiants': etudiants,
			'nombre_colonnes': nombre_colonnes,
			'colonnes': colonnes,
			'lignes_saisie': lignes_saisie,
			'combinaisons': combinaisons,
			'resume_saisie': resume_saisie,
			'auto_reprise_count': auto_reprise_count,
			'message_reprise': message_reprise,
			'saved': saved,
		}),
	)


@login_required
def vue_presences_cours(request):
	classes = Classe.objects.order_by('numero', 'nom')
	cours_liste = Cours.objects.order_by('code')
	synthese_globale = []
	synthese_par_classe = []

	aggregat_global = (
		PresenceEtudiant.objects.values(
			'etudiant__classe_id',
			'etudiant__classe__numero',
			'etudiant__classe__nom',
			'etudiant__cours_id',
			'etudiant__cours__code',
			'statut',
		)
		.annotate(n=Count('id'))
		.order_by('etudiant__classe__numero', 'etudiant__cours__code')
	)

	map_global = {}
	for row in aggregat_global:
		key = (row['etudiant__classe_id'], row['etudiant__cours_id'])
		if key not in map_global:
			map_global[key] = {
				'classe_id': row['etudiant__classe_id'],
				'classe_label': f"R{row['etudiant__classe__numero']} {(row['etudiant__classe__nom'] or '').strip()}".strip(),
				'cours_id': row['etudiant__cours_id'],
				'cours_code': row['etudiant__cours__code'],
				'P': 0,
				'A': 0,
				'AE': 0,
			}

		statut = row['statut']
		if statut in {'P', 'A', 'AE'}:
			map_global[key][statut] += row['n']

	for item in map_global.values():
		item['TOTAL'] = item['P'] + item['A'] + item['AE']
		synthese_globale.append(item)

	synthese_globale.sort(key=lambda x: (x['classe_label'], x['cours_code']))

	aggregat_classes = (
		PresenceEtudiant.objects.values(
			'etudiant__classe_id',
			'etudiant__classe__numero',
			'etudiant__classe__nom',
			'statut',
		)
		.annotate(n=Count('id'))
		.order_by('etudiant__classe__numero')
	)

	map_classes = {}
	for row in aggregat_classes:
		key = row['etudiant__classe_id']
		if key not in map_classes:
			map_classes[key] = {
				'classe_id': row['etudiant__classe_id'],
				'classe_label': f"R{row['etudiant__classe__numero']} {(row['etudiant__classe__nom'] or '').strip()}".strip(),
				'P': 0,
				'A': 0,
				'AE': 0,
			}

		statut = row['statut']
		if statut in {'P', 'A', 'AE'}:
			map_classes[key][statut] += row['n']

	for item in map_classes.values():
		item['TOTAL'] = item['P'] + item['A'] + item['AE']
		if item['TOTAL'] > 0:
			item['TAUX_ABSENCE'] = round((item['A'] / item['TOTAL']) * 100, 1)
		else:
			item['TAUX_ABSENCE'] = 0
		synthese_par_classe.append(item)

	synthese_par_classe.sort(key=lambda x: x['classe_label'])

	classe_id = request.GET.get('classe_id')
	cours_id = request.GET.get('cours_id')

	classe = None
	cours = None
	etudiants = []
	nombre_colonnes = 0
	dates = []
	statuts_map = {}
	lignes = []
	resume_selection = None

	if classe_id and cours_id:
		classe = get_object_or_404(Classe, id=classe_id)
		cours = get_object_or_404(Cours, id=cours_id)
		nombre_colonnes = _nombre_colonnes(cours)

		etudiants = list(
			Etudiant.objects.filter(classe_id=classe.id, cours_id=cours.id).order_by('nom', 'prenom')
		)

		dates = list(
			Presence.objects.filter(classe_id=classe.id, cours_id=cours.id)
			.order_by('date')
			.values_list('date', flat=True)[:nombre_colonnes]
		)

		presences_etudiants = PresenceEtudiant.objects.filter(
			etudiant__classe_id=classe.id,
			etudiant__cours_id=cours.id,
			date__in=dates,
		).select_related('etudiant')

		for ligne in presences_etudiants:
			statuts_map[(ligne.etudiant_id, ligne.date)] = ligne.statut

		colonnes = []
		for i in range(1, nombre_colonnes + 1):
			date = dates[i - 1] if i - 1 < len(dates) else None
			colonnes.append({'index': i, 'date': date})

		for etudiant in etudiants:
			statuts = []
			count_p = 0
			count_a = 0
			count_ae = 0
			for col in colonnes:
				if col['date'] is None:
					statuts.append('-')
				else:
					statut = statuts_map.get((etudiant.id, col['date']), '-')
					statuts.append(statut)
					if statut == 'P':
						count_p += 1
					elif statut == 'A':
						count_a += 1
					elif statut == 'AE':
						count_ae += 1

			if count_a >= 3:
				couleur = 'red'
			elif count_a == 2:
				couleur = 'orange'
			elif count_p > 0:
				couleur = 'green'
			else:
				couleur = 'black'

			lignes.append(
				{
					'etudiant': etudiant,
					'statuts': statuts,
					'count_p': count_p,
					'count_a': count_a,
					'count_ae': count_ae,
					'couleur': couleur,
				}
			)

		resume_selection = {
			'P': sum(l['count_p'] for l in lignes),
			'A': sum(l['count_a'] for l in lignes),
			'AE': sum(l['count_ae'] for l in lignes),
		}
		resume_selection['TOTAL'] = resume_selection['P'] + resume_selection['A'] + resume_selection['AE']
	else:
		colonnes = []

	return render(
		request,
		'academics/vue_presences_cours.html',
		_ctx('synthese', {
			'classes': classes,
			'cours_liste': cours_liste,
			'classe': classe,
			'cours': cours,
			'etudiants': etudiants,
			'nombre_colonnes': nombre_colonnes,
			'colonnes': colonnes,
			'lignes': lignes,
			'resume_selection': resume_selection,
			'synthese_globale': synthese_globale,
			'synthese_par_classe': synthese_par_classe,
		}),
	)
