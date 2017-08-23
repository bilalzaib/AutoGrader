from django.contrib import admin

# Register your models here.
from .models import Section,Assignment

admin.site.register(Section)
admin.site.register(Assignment)