from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.core import serializers

from .models import Course
from .reports import get_course_student_stat,CourseReport

@staff_member_required
def course_students_stat(request, course_id):
    course = Course.objects.get(id = course_id)
    course_student_data = get_course_student_stat(course)

    return render(request, 'reports/course_students_stat.html', {
        'course_student_data': course_student_data,
        'course': course,
        'generated_on': timezone.now()
    })

@staff_member_required
def course_report(request, course_id):
    course = Course.objects.get(id = course_id)
    report = CourseReport()
    column_chart_data = report.get_data_for_column_chart(course)
    stack_column_chart_data = report.get_data_for_stack_column_chart(course)

    return render(request, 'reports/course_report.html', {
        'column_chart_data': column_chart_data,
        'stack_column_chart_data': stack_column_chart_data,
        'course': course
    })

