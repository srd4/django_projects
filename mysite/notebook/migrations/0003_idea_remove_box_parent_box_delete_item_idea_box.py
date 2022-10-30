# Generated by Django 4.0.7 on 2022-10-22 03:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notebook', '0002_alter_box_parent_box'),
    ]

    operations = [
        migrations.CreateModel(
            name='Idea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Idea_text', models.TextField(max_length=280)),
            ],
        ),
        migrations.RemoveField(
            model_name='box',
            name='parent_box',
        ),
        migrations.DeleteModel(
            name='Item',
        ),
        migrations.AddField(
            model_name='idea',
            name='box',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='notebook.box'),
        ),
    ]
