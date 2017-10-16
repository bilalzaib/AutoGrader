import statistics
from .models import *
import dateutil.relativedelta
from datetime import timedelta

def get_course_student_stat(course):
    assignments = Assignment.objects.filter(course=course)
    students = Student.objects.filter(courses=course).order_by('user__email')

    course_student_data = []
    for student in students:

        student_submission_count = 0
        completed_assignments = 0
        total_marks_in_assignments = 0
        total_time_taken = timedelta(seconds = 0)

        for assignment in assignments:
            submission = Submission.objects.filter(student=student, assignment=assignment).order_by("-publish_date")
            student_submission_count += len(submission)
            if submission.count() !=0:      #Completed Assignments
                completed_assignments += 1
                submission = submission.first()
                total_marks_in_assignments += submission.get_score()
                delta = submission.publish_date - assignment.open_date
                total_time_taken = total_time_taken + delta

        late_days_remaining = student.get_late_days_left(course)
        average_marks = total_marks_in_assignments/completed_assignments
        average_submissions = student_submission_count//completed_assignments
        average_time_taken = total_time_taken/(completed_assignments)
        average_time_taken -= timedelta(microseconds=average_time_taken.microseconds)
        course_student_data.append([student, completed_assignments, late_days_remaining, average_marks, average_submissions, average_time_taken])

    return course_student_data
