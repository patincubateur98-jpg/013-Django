from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def deconnexion(request):
	logout(request)
	return redirect('accounts:login')


@login_required
def acces_refuse(request):
	return render(request, 'accounts/acces_refuse.html')
