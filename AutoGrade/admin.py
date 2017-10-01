from django.conf import settings
from django.contrib import admin
from django.db.models import Max, Count
from django.contrib.auth.models import User
from django import forms
from .models import *
from django.contrib import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse

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

class CourseStudentsInline(admin.TabularInline):
    verbose_name = "Enrolled Student"
    verbose_name_plural = "Enrolled Students"
    model = Student.courses.through
    fields = ['student_name', 'student_email', 'student_username', 'student_roll_number']
    readonly_fields = ['student_name', 'student_email', 'student_username', 'student_roll_number']
    extra = 0
    classes = ['collapse']

    def has_add_permission(self, request):
        return False

    def student_username(self, instance):
        return instance.student.user.username
    student_username.short_description = 'student username'

    def student_roll_number(self, instance):
        return instance.student.get_roll_number()
    student_roll_number.short_description = 'student roll number'

    def student_email(self, instance):
        return instance.student.user.email
    student_email.short_description = 'student email'

    def student_name(self, instance):
        return instance.student.user.first_name + " " + instance.student.user.last_name
    student_name.short_description = 'student name'

@admin.register(Course)
class CourseModelAdmin(admin.ModelAdmin):
    inlines = [CourseStudentsInline,]

    # This will hide object name from tabular inline.
    class Media:
        css = { "all" : ("css/hide_admin_original.css",) }

    def get_queryset(self, request):
        qs = super(CourseModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(instructor__user=request.user)

    list_display = ('name', 'enroll_key', 'instructor')
    exclude = ('courses', )

@admin.register(Student)
class StudentModelAdmin(admin.ModelAdmin):
    #inlines = [UserInline,]

    def student_loginas(self, obj):
        return '<a target="_blank" href="' + reverse("home") + 'loginas/' + str(obj.id) + '">Login as ' + obj.user.username + '</a>'

    student_loginas.short_description = 'Login as Student'
    student_loginas.allow_tags = True

    def get_queryset(self, request):
        qs = super(StudentModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(courses__instructor__user=request.user)

    list_display = ('student_username', 'student_firstname', 'student_lastname', 'student_email', 'student_loginas')
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'user__username']

class SubmissionInline(admin.TabularInline):
    model = Submission
    fieldsets = (
        (None, {
            'fields': ('student','passed', 'failed', 'publish_date')
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
        if not self.current_user.is_superuser:
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

    def assignment_report(self, obj):
        return '<a target="_blank" href="' + reverse("home") + 'assignment_report/' + str(obj.id) + '">Show Report</a>'

    assignment_report.short_description = 'Show Report'
    assignment_report.allow_tags = True

    form = AssignmentFormAdmin
    inlines = [OtherFilesInline,]
    list_display = ('title', 'course', 'due_date', 'open_date', 'assignment_report')
    list_filter = ('course', )
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
    list_display = ('assignment', 'assignment_course', 'student', 'publish_date', 'passed', 'failed')

@admin.register(AssignmentExtension)
class AssignmentExtensionModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(AssignmentExtensionModelAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(assignment__course__instructor__user=request.user)

    # list_filter = ('assignment', )
    list_display = ('student', 'assignment', 'days')
