from django.db import migrations

def populate_db(apps, schema_editor):
    Report = apps.get_model('projectmanagement', 'Report')

    draw_report_by_sub = Report(name="Draw Report By Sub")
    draw_report_by_sub.save()

class Migration(migrations.Migration):
    dependencies = [
        ('projectmanagement', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_db),
    ]
