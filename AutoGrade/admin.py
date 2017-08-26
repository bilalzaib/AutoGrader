from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Instructor)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(Assignment)
admin.site.register(Submission)