# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-10 10:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(blank=True, max_length=300, null=True)),
                ('docfile', models.FileField(blank=True, null=True, upload_to='uploads/')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('categories', models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name='Index',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_id', models.IntegerField()),
                ('invertedIndex', models.TextField(null=True)),
                ('name', models.TextField(null=True)),
            ],
        ),
    ]
