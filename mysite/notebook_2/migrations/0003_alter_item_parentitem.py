# Generated by Django 4.1.2 on 2022-11-24 20:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notebook_2', '0002_alter_container_owner_alter_item_owner_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='parentItem',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='notebook_2.item'),
        ),
    ]
