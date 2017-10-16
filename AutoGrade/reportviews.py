from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from .models import *
from .reports import *

@staff_member_required
def course_students_stat(request, course_id):
    course = Course.objects.get(id = course_id)
    course_student_data = get_course_student_stat(course)

    return render(request, 'report/course_students_stat.html', {
        'course_student_data': course_student_data,
        'course': course,
        'generated_on': timezone.now()
    })

