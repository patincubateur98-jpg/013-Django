from django.http import HttpResponse


def home(request):
	return HttpResponse("PCNC Fusion Django est prêt ✅")
