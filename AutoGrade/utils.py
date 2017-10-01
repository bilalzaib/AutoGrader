from .models import Course, Assignment, DueDate_Extension
from django.utils import timezone
from datetime import timedelta

def count_remaining_late_days(student, course_id):
    course = Course.objects.get(id = course_id)

    num_count = DueDate_Extension.objects.filter(student = student, course_id = course_id).count()
    if num_count !=0:
        requests = DueDate_Extension.objects.filter(student=student, course_id=course_id)
        days = 0
        for request in requests:
            diff = request.due_date - request.assignment.due_date
            days += diff.days
        days = course.late_days - days
    else:
        days = course.late_days

    return days

def late_assignment_days(assignment, student, course_id):
    course = Course.objects.get(id=course_id)
    diff = timezone.now() - assignment.get_correct_due_date(student)
    days = count_remaining_late_days(student, course_id)
    if  days == 0 or diff.days >= days:
        return 0
    return int(diff.total_seconds() / (3600 * 24)) + 1