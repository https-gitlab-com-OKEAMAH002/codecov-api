# Generated by Django 2.1.3 on 2019-06-18 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Version',
            fields=[
                ('version', models.TextField(db_column='version', primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'version',
            },
        ),
    ]
