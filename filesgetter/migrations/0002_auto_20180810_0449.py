# Generated by Django 2.0.5 on 2018-08-10 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('filesgetter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parameters',
            name='gross_weight',
            field=models.IntegerField(),
        ),
    ]
