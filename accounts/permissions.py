from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def user_has_role(user, allowed_roles):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    roles = {nom.upper() for nom in allowed_roles}
    groupes = {g.upper() for g in user.groups.values_list('name', flat=True)}
    return bool(groupes.intersection(roles))


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_has_role(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)

            messages.error(request, "Accès refusé : droits insuffisants.")
            return redirect('accounts:acces_refuse')

        return wrapper

    return decorator
