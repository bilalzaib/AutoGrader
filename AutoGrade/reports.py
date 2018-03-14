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
        average_marks = 0
        average_submissions = 0
        average_time_taken = 0
        if completed_assignments:
            average_marks = total_marks_in_assignments/completed_assignments
            average_submissions = student_submission_count/float(completed_assignments)
            average_time_taken = total_time_taken/(completed_assignments)
            average_time_taken -= timedelta(microseconds=average_time_taken.microseconds)

        course_student_data.append([student, completed_assignments, late_days_remaining, average_marks, average_submissions, average_time_taken])

    return course_student_data

class CourseReport:

    def get_data_for_column_chart(self, course):
        assignments = Assignment.objects.filter(course=course)
        rows = []
        for assignment in assignments:
            submission_count = Submission.objects.filter(assignment=assignment).count()
            date = assignment.due_date.strftime('%Y-%m-%d')
            rows.append([date, submission_count])
        return rows

    def get_data_for_stack_column_chart(self,course):
        assignments = Assignment.objects.filter(course=course)

        rows = []

        for assignment in assignments:
            latest_submissions = assignment.get_student_and_latest_submissions()
            list_of_student_score = []
            for submission, student, student_submission_count in latest_submissions:
                if submission is not None:
                    list_of_student_score.append(submission.get_score())

            as_str = "Assignment-" + str(assignment.id)
            date = assignment.due_date.strftime('%Y-%m-%d')
            minim = 0
            maxim = 0
            mean = 0
            if len(list_of_student_score) != 0:
                minim = min(list_of_student_score)
                maxim = max(list_of_student_score)
                mean = statistics.mean(list_of_student_score)
            rows.append([date, {'v':minim, 'f':str(minim)}, {'v':mean-minim, 'f':str(format(mean, '.2f'))}, {'v':maxim-mean, 'f':str(maxim)}])

        return rows