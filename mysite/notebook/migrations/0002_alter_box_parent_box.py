# Generated by Django 4.0.7 on 2022-10-20 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notebook', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='parent_box',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='notebook.box'),
        ),
    ]
