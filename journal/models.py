from django.db import models
from django.utils import timezone


class Journal(models.Model):
	date_heure = models.DateTimeField(default=timezone.now)
	type_action = models.CharField(max_length=20)
	table_concernee = models.CharField(max_length=50)
	id_enregistrement = models.IntegerField()
	ancien_donnees = models.TextField(blank=True, null=True)
	nouvel_donnees = models.TextField(blank=True, null=True)

	class Meta:
		db_table = 'journal'
		ordering = ['-date_heure']

	def __str__(self):
		return f"{self.type_action} {self.table_concernee} #{self.id_enregistrement}"
