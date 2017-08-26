from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

class Section(models.Model):
    DEFAULT_PK = 1
    sec_name = models.CharField(max_length=10)
    rand_key = models.IntegerField()

    def __str__(self):
        return self.sec_name

class Assignment(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    as_code = models.CharField(max_length = 5)
    as_text = models.CharField(max_length=1000)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.as_code

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, default = Section.DEFAULT_PK)

@receiver(post_save, sender=User)
def update_student(sender, instance, created, **kwargs):
    if created:
        Student.objects.create(user=instance)
    instance.student.save()