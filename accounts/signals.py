from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def creer_groupes_roles(sender, **kwargs):
    for nom in ('ADMIN', 'COORDINATEUR', 'TUTEUR'):
        Group.objects.get_or_create(name=nom)
