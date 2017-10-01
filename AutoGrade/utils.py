from .models import Course, Assignment, DueDate_Extension
from django.utils import timezone
from datetime import timedelta

def count_remaining_late_days(assignment, student, course_id):
    course = Course.objects.get(id = course_id)
    diff = timezone.now() - assignment.due_date
    if diff.days > course.late_days:
        return 0

    #one condition remaining to solve
    """try:    
        re = Request_Extension.objects.get(student=student, assignment=assignment)
        diff = timezone.now() - re.due_date
        if re and diff.days:
                                                            
    except (Request_Extension.DoesNotExist):
        pass"""

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