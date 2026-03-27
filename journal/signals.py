import json
from datetime import date, datetime
from decimal import Decimal

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from journal.models import Journal


IGNORED_APPS = {
    'admin',
    'auth',
    'contenttypes',
    'sessions',
    'messages',
    'staticfiles',
}


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _instance_to_dict(instance):
    data = {}
    for field in instance._meta.concrete_fields:
        data[field.name] = _serialize_value(getattr(instance, field.attname))
    return data


def _table_name(instance):
    return instance._meta.db_table


def _is_auditable_model(sender):
    if sender is Journal:
        return False
    if sender._meta.app_label in IGNORED_APPS:
        return False
    return True


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not _is_auditable_model(sender):
        return
    if instance.pk is None:
        instance._journal_old_data = None
        return

    old_instance = sender.objects.filter(pk=instance.pk).first()
    instance._journal_old_data = _instance_to_dict(old_instance) if old_instance else None


@receiver(post_save)
def audit_post_save(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    if not _is_auditable_model(sender):
        return

    new_data = _instance_to_dict(instance)
    old_data = getattr(instance, '_journal_old_data', None)

    if created:
        Journal.objects.create(
            type_action='CREATE',
            table_concernee=_table_name(instance),
            id_enregistrement=instance.pk,
            ancien_donnees=None,
            nouvel_donnees=json.dumps(new_data, ensure_ascii=False),
        )
        return

    if old_data == new_data:
        return

    Journal.objects.create(
        type_action='UPDATE',
        table_concernee=_table_name(instance),
        id_enregistrement=instance.pk,
        ancien_donnees=json.dumps(old_data, ensure_ascii=False) if old_data is not None else None,
        nouvel_donnees=json.dumps(new_data, ensure_ascii=False),
    )


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _is_auditable_model(sender):
        return

    old_data = _instance_to_dict(instance)
    Journal.objects.create(
        type_action='DELETE',
        table_concernee=_table_name(instance),
        id_enregistrement=instance.pk,
        ancien_donnees=json.dumps(old_data, ensure_ascii=False),
        nouvel_donnees=None,
    )
