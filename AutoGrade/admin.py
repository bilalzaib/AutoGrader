from django.contrib import admin
from django.db.models import Max, Count
from django.contrib.auth.models import User
from django import forms
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


class AssignmentFormAdmin(forms.ModelForm):
    # Receive from get_form of AssignmentModalAdmin
    current_user = None
    
    def __init__(self, *args, **kwargs):
        super(AssignmentFormAdmin, self).__init__(*args, **kwargs)
        instructor = Instructor.objects.filter(user=self.current_user).first()
        self.fields['course'].queryset = Course.objects.filter(instructor=instructor)

    class Meta:
        fields = '__all__'
        model = Assignment

class OtherFilesInline(admin.StackedInline):
    model       = OtherFile
    #max_num    = 10
    #extra      = 0

# Hide Other File from admin index
class OtherFileAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

admin.site.register(OtherFile, OtherFileAdmin)

@admin.register(Assignment) 
class AssignmentModelAdmin(admin.ModelAdmin):    
    #form = AssignmentFormAdmin
    inlines = [OtherFilesInline,]

    def get_form(self, request, *args, **kwargs):
         form = super(AssignmentModelAdmin, self).get_form(request, *args, **kwargs)
         form.current_user = request.user
         return form

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
