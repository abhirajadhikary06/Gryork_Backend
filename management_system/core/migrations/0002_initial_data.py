# This is a manual migration file. Run `python manage.py makemigrations --empty core` to create 0002, then replace with this.
from django.db import migrations

def create_predefined_departments(apps, schema_editor):
    Department = apps.get_model('core', 'Department')
    departments = ['Civil', 'Electrical', 'Mechanical', 'Plumbing']
    for name in departments:
        Department.objects.get_or_create(name=name)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),  # Adjust based on your first migration
    ]
    operations = [
        migrations.RunPython(create_predefined_departments),
    ]