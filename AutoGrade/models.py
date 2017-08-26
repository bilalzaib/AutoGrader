from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime    
import string
import random

def assignment_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'uploads/assignment/course_{0}/{1}/{2}'.format(instance.course.id, instance.title, filename)

def submission_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'uploads/submission/student_{0}/course_{1}/assignment_{2}/{3}'.format(instance.user.id, instance.course.id, instance.assignment.id, filename)

def submission_key():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))

def enroll_key():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

# Create your models here.

class Section(models.Model):
    pass


class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # name, email, password

    def __str__(self):
        return self.user.username
    
class Course(models.Model):
    instructor = models.ForeignKey(Instructor, null=False, default=None)
    name = models.CharField(max_length=32)
    enroll_key = models.CharField(max_length=8, default=enroll_key, unique=True) # Secret key to enroll
    course_id = models.CharField(max_length=6) # CS101

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # name, email, password
    submission_pass = models.CharField(max_length=12, default=submission_key) 
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return self.user.username

class Assignment(models.Model):
    course          = models.ForeignKey(Course, on_delete=models.CASCADE, null=False, default=None)
    
    title           = models.CharField(max_length=32, null=False, default=None)
    description     = models.TextField(max_length=512, null=True, default=None)
    
    # Files
    instructor_test = models.FileField(upload_to=assignment_directory_path, null=False, default=None)
    student_test    = models.FileField(upload_to=assignment_directory_path, null=False, default=None)
    config_file     = models.FileField(upload_to=assignment_directory_path, null=False, default=None)
    assignment_file = models.FileField(upload_to=assignment_directory_path, null=False, default=None)

    due_date = models.DateTimeField('due date', default=datetime.now)
    publish_date = models.DateTimeField('date published', default=datetime.now)

    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment      = models.ForeignKey(Assignment)
    student         = models.ForeignKey(Student)
    submission_file = models.FileField(upload_to=submission_directory_path, null=False)
    score           = models.IntegerField()

"""
@receiver(post_save, sender=User)
def update_student(sender, instance, created, **kwargs):
    if created:
        Student.objects.create(user=instance)
    instance.student.save()

"""