# Generated by Django 4.1.3 on 2023-05-25 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertgroup',
            name='name',
            field=models.CharField(default='AAPL', max_length=5),
        ),
        migrations.AlterField(
            model_name='alertgroup',
            name='alert',
            field=models.IntegerField(),
        ),
    ]
