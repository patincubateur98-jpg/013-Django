from django.db import models


class Classe(models.Model):
	numero = models.IntegerField()
	nom = models.CharField(max_length=100, blank=True, null=True)
	archived = models.BooleanField(default=False)

	class Meta:
		db_table = 'classe'
		ordering = ['numero', 'nom']

	def __str__(self):
		classe_nom = self.nom or ''
		return f"R{self.numero} {classe_nom}".strip()


class Cours(models.Model):
	code = models.CharField(max_length=10, unique=True)
	nom = models.CharField(max_length=100, blank=True, null=True)

	class Meta:
		db_table = 'cours'
		ordering = ['code']

	def __str__(self):
		return self.code


class Tuteur(models.Model):
	genre = models.CharField(max_length=10, blank=True, null=True)
	nom = models.CharField(max_length=100)
	prenom = models.CharField(max_length=100, blank=True, null=True)
	telephone = models.CharField(max_length=20, blank=True, null=True)
	email = models.EmailField(max_length=120, unique=True)
	role = models.CharField(max_length=50, blank=True, null=True, default='Formateur')
	username = models.CharField(max_length=80, unique=True, blank=True, null=True)
	password_hash = models.CharField(max_length=200, blank=True, null=True)
	is_active = models.BooleanField(default=True)
	classe_affectee = models.CharField(max_length=100, blank=True, null=True)

	class Meta:
		db_table = 'tuteur'
		ordering = ['nom', 'prenom']

	def __str__(self):
		return f"{self.nom} {self.prenom or ''}".strip()


class Etudiant(models.Model):
	genre = models.CharField(max_length=10, blank=True, null=True)
	nom = models.CharField(max_length=100)
	prenom = models.CharField(max_length=100, blank=True, null=True)
	email = models.EmailField(max_length=120)
	telephone = models.CharField(max_length=20, blank=True, null=True)
	presence = models.CharField(max_length=2, blank=True, null=True)
	classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name='etudiants')
	cours = models.ForeignKey(Cours, on_delete=models.PROTECT, related_name='etudiants')
	tuteur = models.ForeignKey(Tuteur, on_delete=models.SET_NULL, related_name='etudiants', blank=True, null=True)

	class Meta:
		db_table = 'etudiant'
		ordering = ['nom', 'prenom']

	def __str__(self):
		return f"{self.nom} {self.prenom or ''}".strip()


class Presence(models.Model):
	date = models.DateField()
	cours = models.ForeignKey(Cours, on_delete=models.PROTECT, related_name='presences_dates')
	classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name='presences')

	class Meta:
		db_table = 'presence'
		ordering = ['date']

	def __str__(self):
		return f"{self.date} - {self.cours_id}"


class PresenceEtudiant(models.Model):
	etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='presences')
	date = models.DateField()
	statut = models.CharField(max_length=2)
	commentaire = models.TextField(blank=True, null=True)

	class Meta:
		db_table = 'presence_etudiant'
		ordering = ['date']

	def __str__(self):
		return f"{self.etudiant_id} {self.date} {self.statut}"


class TuteurPresence(models.Model):
	tuteur = models.ForeignKey(Tuteur, on_delete=models.CASCADE, related_name='presences')
	date = models.DateField()
	statut = models.CharField(max_length=2)
	commentaire = models.TextField(blank=True, null=True)

	class Meta:
		db_table = 'tuteur_presence'
		ordering = ['date']

	def __str__(self):
		return f"{self.tuteur_id} {self.date} {self.statut}"
