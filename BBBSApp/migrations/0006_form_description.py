# Generated by Django 3.2.8 on 2022-07-17 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BBBSApp', '0005_alter_developmental_difficulties_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='description',
            field=models.TextField(max_length=500, null=True),
        ),
    ]
