from __future__ import unicode_literals

from django.db import models


class Document(models.Model):
    category = models.CharField(max_length=300, blank=True, null=True)
    docfile = models.FileField(upload_to='uploads/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True,
                                     auto_now=False)  # but in forms, set blank=True,form can be left.
    categories = models.CharField(max_length=120, blank=False, null=False)


class Index(models.Model):
    video_id = models.IntegerField(null=False,primary_key=True)
    invertedIndex = models.TextField(null=True)
    name = models.TextField(null=True)

