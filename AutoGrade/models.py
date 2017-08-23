from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class Section(models.Model):
    sec_name = models.CharField(max_length=10)
    rand_key = models.IntegerField()

    def __str__(self):
        return self.sec_name

class Assignment(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    assignment_text = models.CharField(max_length=1000)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.assignment_text