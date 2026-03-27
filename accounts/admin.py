from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist


ROLE_GROUPS = ('ADMIN', 'COORDINATEUR', 'TUTEUR')


def _get_or_create_role_group(role_name):
	group, _ = Group.objects.get_or_create(name=role_name)
	return group


def _set_single_role(user, role_name):
	role_groups = list(Group.objects.filter(name__in=ROLE_GROUPS))
	if role_groups:
		user.groups.remove(*role_groups)
	user.groups.add(_get_or_create_role_group(role_name))


class UserAdmin(BaseUserAdmin):
	list_display = BaseUserAdmin.list_display + ('roles_affiches',)
	list_filter = BaseUserAdmin.list_filter + ('groups',)
	actions = ('assigner_admin', 'assigner_coordinateur', 'assigner_tuteur')

	@admin.display(description='Rôles')
	def roles_affiches(self, obj):
		roles = obj.groups.filter(name__in=ROLE_GROUPS).values_list('name', flat=True)
		texte = ', '.join(sorted(roles))
		return texte or 'Aucun'

	@admin.action(description='Assigner le rôle ADMIN')
	def assigner_admin(self, request, queryset):
		for user in queryset:
			_set_single_role(user, 'ADMIN')

	@admin.action(description='Assigner le rôle COORDINATEUR')
	def assigner_coordinateur(self, request, queryset):
		for user in queryset:
			_set_single_role(user, 'COORDINATEUR')

	@admin.action(description='Assigner le rôle TUTEUR')
	def assigner_tuteur(self, request, queryset):
		for user in queryset:
			_set_single_role(user, 'TUTEUR')


try:
	admin.site.unregister(User)
except ObjectDoesNotExist:
	pass

admin.site.register(User, UserAdmin)
