# Generated by Django 4.2.11 on 2024-07-24 18:49

from django.db import migrations


def update_locale_code(apps, schema_editor):
    UXActionLog = apps.get_model("uxactionlog", "UXActionLog")
    Locale = apps.get_model("base", "Locale")

    for log in UXActionLog.objects.filter(action_type="LLM Dropdown Select"):
        data = log.data
        if "targetLanguage" in data:
            locale_name = data.pop("targetLanguage")
            locale_code = Locale.objects.get(name=locale_name).code
            data["localeCode"] = locale_code
            log.data = data
            log.save()


class Migration(migrations.Migration):
    dependencies = [
        ("uxactionlog", "0001_initial"),
        (
            "base",
            "0001_squashed_0154_auto_20200206_1736",
        ),  # Ensure the Locale model's migration is applied first
    ]

    operations = [
        migrations.RunPython(
            code=update_locale_code,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
