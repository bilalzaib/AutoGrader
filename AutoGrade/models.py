from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .storage import OverwriteStorage

from os.path import basename

from datetime import datetime    
import string
import random
import time
import zipfile
import json
import os

def assignment_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'uploads/assignment/course_{0}/{1}/{2}'.format(instance.course.id, instance.title.replace(" ","-").lower(), filename)

def submission_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H%M%S')
    return 'uploads/submission/student_{0}/assignment_{1}/{2}{3}'.format(instance.student.id, instance.assignment.id, st, filename)

def submission_key():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))

def enroll_key():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

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
    instructor_test = models.FileField(upload_to=assignment_directory_path, null=False, default=None, storage=OverwriteStorage())
    student_test    = models.FileField(upload_to=assignment_directory_path, null=False, default=None, storage=OverwriteStorage())
    #config_file     = models.FileField(upload_to=assignment_directory_path, null=False, default=None, storage=OverwriteStorage())
    assignment_file = models.FileField(upload_to=assignment_directory_path, null=False, default=None, storage=OverwriteStorage())

    #assignment_files = FilerFileField(related_name="filer_assignment_files", null=True)

    total_points    = models.IntegerField(default=25)
    timeout         = models.IntegerField(default=3)

    open_date = models.DateTimeField('open date', default=datetime.now)
    due_date = models.DateTimeField('due date', default=datetime.now)
    publish_date = models.DateTimeField('date published', default=datetime.now)

    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment      = models.ForeignKey(Assignment)
    student         = models.ForeignKey(Student)
    submission_file = models.FileField(upload_to=submission_directory_path, null=False)
    passed          = models.IntegerField(default=0)
    failed          = models.IntegerField(default=0)
    percent         = models.FloatField(default=0)
    publish_date    = models.DateTimeField('date published', default=datetime.now)

    def get_log_file(self):
        return self.submission_file.url.replace(".zip","")  + "/test-results.log"

# Create zip file of Assignment
@receiver(post_save, sender=Assignment)
def create_assignment_zip_file(sender, instance, created, **kwargs):
    assignment_directory = assignment_directory_path(instance, "")
    
    # save in assignment folder as "assignment[ID].zip" eg. "assignment2.zip"
    zip_full_path = assignment_directory + "assignment" + str(instance.id) + ".zip"

    # Creating student zip file
    zip_file = zipfile.ZipFile(zip_full_path, 'w', zipfile.ZIP_DEFLATED)
    
    assignment_id = int(instance.id);

    student_config = {
        "assignment"       : int(assignment_id),
        "modifiable_files" : [basename(instance.assignment_file.url)],
        "student_tests"    : [basename(instance.student_test.url)],
        "timeout"          : int(instance.timeout),
        "total_points"     : int(instance.total_points)
    }

    student_config_file = assignment_directory + "config.json";
    with open(student_config_file, 'w') as file:
            json.dump(student_config, file, indent=4)

    files = []
    files.append(instance.student_test.url)
    files.append(instance.assignment_file.url)
    files.append(student_config_file)
    files.append("uploads/assignment/submit.py")

    for file in files:
        zip_file.write(file, os.path.basename(file))
    zip_file.close()
