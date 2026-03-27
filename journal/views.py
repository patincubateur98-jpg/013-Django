from django.shortcuts import render

from accounts.permissions import role_required

from .models import Journal


@role_required('ADMIN', 'COORDINATEUR')
def historique(request):
	action = request.GET.get('action', '').strip().upper()
	table = request.GET.get('table', '').strip()

	entries = Journal.objects.all().order_by('-date_heure')
	if action:
		entries = entries.filter(type_action=action)
	if table:
		entries = entries.filter(table_concernee__icontains=table)

	entries = entries[:500]
	tables = list(Journal.objects.values_list('table_concernee', flat=True).distinct().order_by('table_concernee'))

	return render(
		request,
		'journal/historique.html',
		{
			'active_nav': 'journal',
			'entries': entries,
			'action': action,
			'table': table,
			'tables': tables,
		},
	)
