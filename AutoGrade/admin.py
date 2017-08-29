from django.contrib import admin
from django.db.models import Max, Count
from django.contrib.auth.models import User

from .models import *

class UserInline(admin.StackedInline):
    model = User

@admin.register(Instructor) 
class InstructorModelAdmin(admin.ModelAdmin):
    #inlines = [UserInline,]

    def get_queryset(self, request):
        qs = super(InstructorModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()

@admin.register(Course) 
class CourseModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(CourseModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(instructor__user=request.user)

@admin.register(Student) 
class StudentModelAdmin(admin.ModelAdmin):
    #inlines = [UserInline,]

    def get_queryset(self, request):
        qs = super(StudentModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(courses__instructor__user=request.user)

class SubmissionInline(admin.TabularInline):
    model = Submission
    fieldsets = (
        (None, {
            'fields': ('student','passed', 'failed', 'percent', 'publish_date')
        }),
    )

    def get_queryset(self, request):
        assignment_id = request.path.split('/')[4]
        if assignment_id.isdigit():
            result = Submission.objects.filter(assignment=assignment_id).annotate(Count('student')).order_by('-publish_date')
            return result
        else:
            qs = super(SubmissionInline, self).get_queryset(request)
            return qs


@admin.register(Assignment) 
class AssignmentModelAdmin(admin.ModelAdmin):
    #inlines = [SubmissionInline,]

    def get_queryset(self, request):
        qs = super(AssignmentModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(course__instructor__user=request.user)

@admin.register(Submission) 
class SubmissionModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(SubmissionModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(assignment__course__instructor__user=request.user)
