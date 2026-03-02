from django.db import models
from django.utils import timezone


class ImportLog(models.Model):
	date_heure = models.DateTimeField(default=timezone.now)
	fichier = models.CharField(max_length=255)
	statut = models.CharField(max_length=20)
	lignes_total = models.IntegerField(blank=True, null=True)
	lignes_ajoutees = models.IntegerField(blank=True, null=True)
	lignes_doublons = models.IntegerField(blank=True, null=True)
	lignes_erreurs = models.IntegerField(blank=True, null=True)
	details = models.TextField(blank=True, null=True)

	class Meta:
		db_table = 'import_log'
		ordering = ['-date_heure']

	def __str__(self):
		return f"{self.fichier} - {self.statut}"
