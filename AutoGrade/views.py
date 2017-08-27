
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.utils import timezone
from django.utils.encoding import smart_str

from .models import Student, Course, Assignment, Submission
from .forms import SignUpForm, EnrollForm

from django.http import JsonResponse

import json
import zipfile
import shutil
import logging
import os
import sys
import re
import time
from datetime import datetime

@login_required(login_url='login')
def home(request):
    user = User.objects.get(pk=request.user.id)
    student = Student.objects.filter(user=user)[0]

    form = EnrollForm()
    if request.method == "POST":
        form = EnrollForm(request.POST)

        if form.is_valid():
            course = form.cleaned_data['course']
            secret_key = form.cleaned_data['secret_key']

            course = Course.objects.filter(enroll_key=secret_key)[0]
            if (course):
                student.courses.add(course)
                student.save()
            else:
                form.add_error('secret_key', "Invalid details")
            redirect('home')

    errors = form.errors or None
    print(student.courses.all())
    return render(request,
                  'home.html',
                  {
                      'courses': student.courses.all(),
                      'form': form,
                      'errors': errors,
                      'student': student
                  }
                  )


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            request.session['username'] = user.username
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def download(request):
    # TODO: break when user try to download Instructor Test file
    path = request.GET.get('path')

    if path.startswith("uploads/assignment/"): # For securing 
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
    
    raise Http404


@login_required(login_url='login')
def course(request, course_id, assignment_id=0):
    user = User.objects.get(pk=request.user.id)
    student = Student.objects.filter(user=user)[0]
    course = Course.objects.get(pk=course_id)
    assignments = Assignment.objects.filter(course=course)

    selected_assignment = None
    submission_history = None
    assignment_zip_file = None
    if (assignment_id != 0):
        selected_assignment = Assignment.objects.get(id=assignment_id)
        submission_history = Submission.objects.filter(student=student).order_by("-publish_date")

        assignment_zip_file = os.path.split(selected_assignment.config_file.url)[0] + "/assignment" + str(assignment_id) + ".zip"

    return render(request, 'course.html', {
        'assignment_zip_file': assignment_zip_file,
        'assignment_id': int(assignment_id),
        'course': course,
        'assignments': assignments,
        'selected_assignment': selected_assignment,
        'submission_history': submission_history
    }
    )



def get_score_from_result_line(res_line, total_points):
    # case where we have failures and passes
    match = re.match(r"=*\s(\d*)\sfailed,\s(\d*)\spassed,\s.*", res_line)
    if match:
        failed = int(match.group(1))
        passed = int(match.group(2))
    else:
        match = re.match(r"=*\s(\d*)\spassed.*", res_line)
        if match:
            passed = int(match.group(1))
            failed = 0
        else:
            match = re.match(r"=*\s(\d*)\sfailed.*", res_line)
            if match:
                passed = 0
                failed = int(match.group(1))
            else:
                logging.error("Failed to parse score line: " + res_line)
                # TODO: throw exception

    percent = float(passed) * total_points / (passed+failed)
    return (passed, failed, percent)


def run_student_tests(target_folder, total_points, timeout):
    logging.debug("Running student tests in: " +target_folder)
    cur_directory = os.getcwd()

    logging.debug("Changing directory ... ")
    os.chdir(target_folder)
    score = (0, 0, 0) # passed, failed, percent

    logging.debug("Capturing stdout")
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    import pytest
    pytest.main(['--timeout=' + str(timeout)])
    logging.debug("Restoring stdout")

    sys.stdout = old_stdout
    out = mystdout.getvalue()

    # print out
    res_line = out.splitlines()[-1]
    score = get_score_from_result_line(res_line, total_points)

    logging.debug("Restoring working directory ...")

    logging.debug("Read test line [" + res_line.strip("=") + "]")
    logging.debug("Calculated score: " + str(score))
    os.chdir(cur_directory)

    return (score, out)

def write_student_log(student_assignment_folder, outlog):
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H%M%S')
    out_file = os.path.join(student_assignment_folder, "test-results-" + st + ".log")
    logging.debug("Writing log to: " + out_file)
    with open(out_file, "a") as text_file:
        text_file.write(outlog)

@csrf_exempt
def api(request, action):
    email = request.POST.get('email')
    submission_pass = request.POST.get('submission_pass')

    user = User.objects.filter(email=email)
    if (user):
        student = Student.objects.filter(
            user=user[0], submission_pass=submission_pass)[0]
        if (student):
            if (action == "submit_assignment"):

                if request.method == 'POST':
                    
                    assignment = Assignment.objects.get(id=request.POST.get('assignment'))

                    if timezone.now() > assignment.due_date:
                        response_data = {"status": 200, "type": "SUCCESS",
                         "message": "Assignment submission date expired"}
                    else:
                        submission = Submission(submission_file=request.FILES['submission_file'], 
                            assignment=assignment,
                            student=student)
                        submission.save()

                        submission_file_url = submission.submission_file.url
                        extract_directory = submission_file_url.replace(".zip","/")

                        zip_file = zipfile.ZipFile(submission.submission_file.url, 'r')
                        zip_file.extractall(extract_directory)
                        zip_file.close()

                        # Move Instructor Test File
                        shutil.copy(assignment.instructor_test.url, extract_directory)
                        
                        # TODO: Move Student Test File
                        #shutil.copy(assignment.student_test.url, extract_directory)                        

                        config_data = None
                        with open(assignment.config_file.url) as file:
                            config_data = json.load(file)
                      
                        score, outlog = run_student_tests(extract_directory, config_data['total_points'], config_data['timeout'])
                        write_student_log(extract_directory, outlog)

                        submission.passed  = score[0]
                        submission.failed  = score[1]
                        submission.percent = score[2]

                        submission.save()

                        response_data = {"status": 200, "type": "SUCCESS",
                             "message": score}

                else:
                    response_data = {"status": 400, "type": "ERROR",
                             "message": "Use POST method"}
            else:
                response_data = {"status": 400, "type": "ERROR",
                             "message": "Invalid action"}
        else:
            response_data = {"status": 400, "type": "ERROR",
                             "message": "Invalid student"}
    else:
        response_data = {"status": 400,
                         "type": "ERROR", "message": "Invalid user"}

    return JsonResponse(response_data, safe=False)
