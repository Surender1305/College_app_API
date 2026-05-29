"""
Data migration — sets the group field on all existing Department rows.

This fixes production databases where departments were created before the
group field existed. It runs automatically via 'python manage.py migrate'.

Rules applied:
  - Codes starting with 'IC_'  → group = 'IC'
  - code == 'IC'               → group = 'IC'  (legacy flat IC dept)
  - Everything else            → group = None   (MCA, BCA, BED, CS, ME …)
"""
from django.db import migrations


def set_department_groups(apps, schema_editor):
    Department = apps.get_model('academics', 'Department')

    # All IC sub-departments and the legacy flat IC dept
    Department.objects.filter(code__startswith='IC_').update(group='IC')
    Department.objects.filter(code='IC').update(group='IC')

    # All other departments must have group=None (clear any stale values)
    Department.objects.exclude(code__startswith='IC_').exclude(code='IC').update(group=None)


def reverse_migration(apps, schema_editor):
    Department = apps.get_model('academics', 'Department')
    Department.objects.all().update(group=None)


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0007_add_department_group'),
    ]

    operations = [
        migrations.RunPython(set_department_groups, reverse_migration),
    ]
