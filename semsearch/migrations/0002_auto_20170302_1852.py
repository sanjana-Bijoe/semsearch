# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-02 18:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('semsearch', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='category1',
        ),
        migrations.RemoveField(
            model_name='video',
            name='category2',
        ),
        migrations.RemoveField(
            model_name='video',
            name='category3',
        ),
        migrations.RemoveField(
            model_name='video',
            name='category4',
        ),
        migrations.RemoveField(
            model_name='video',
            name='description',
        ),
        migrations.RemoveField(
            model_name='video',
            name='timestamp',
        ),
        migrations.RemoveField(
            model_name='video',
            name='updated',
        ),
        migrations.RemoveField(
            model_name='video',
            name='video_title',
        ),
    ]