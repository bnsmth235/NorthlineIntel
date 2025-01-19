from django.conf import settings
from django.db import migrations

def create_profiles_for_existing_users(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Profile = apps.get_model('projectmanagement', 'Profile')
    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)

class Migration(migrations.Migration):

    dependencies = [
        ('projectmanagement', '0006_profile'),
    ]

    operations = [
        migrations.RunPython(create_profiles_for_existing_users),
    ]