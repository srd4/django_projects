# Generated by Django 4.1.2 on 2022-10-31 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notebook', '0005_alter_idea_box'),
    ]

    operations = [
        migrations.AddField(
            model_name='idea',
            name='actionable',
            field=models.BooleanField(default=False),
        ),
    ]
