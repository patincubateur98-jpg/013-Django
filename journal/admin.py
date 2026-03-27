from django.contrib import admin

from .models import Journal


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
	list_display = ('date_heure', 'type_action', 'table_concernee', 'id_enregistrement')
	list_filter = ('type_action', 'table_concernee')
	search_fields = ('table_concernee', 'id_enregistrement', 'ancien_donnees', 'nouvel_donnees')
	ordering = ('-date_heure',)
