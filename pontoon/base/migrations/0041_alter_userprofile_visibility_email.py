# Generated by Django 3.2.15 on 2023-05-09 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_remove_changed_entity_locale_entries_for_repository_projects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='visibility_email',
            field=models.CharField(choices=[('Logged-in users', 'Logged-in users'), ('Translators', 'Users with translator rights')], default='Translators', max_length=20, verbose_name='Email address'),
        ),
    ]
