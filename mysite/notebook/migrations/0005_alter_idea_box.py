# Generated by Django 4.0.7 on 2022-10-29 22:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notebook', '0004_rename_idea_text_idea_idea_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='idea',
            name='box',
            field=models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='notebook.box'),
        ),
    ]