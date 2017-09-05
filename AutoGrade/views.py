from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.utils.encoding import force_text
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.utils import timezone
from django.utils.encoding import smart_str
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Student, Course, Assignment, Submission
from .forms import SignUpForm, EnrollForm
from django.contrib import messages
from .grader import run_student_tests

from multiprocessing import Process, Manager, Queue

import mimetypes
import json
import zipfile
import shutil
import logging
import os
import sys
import re
import time
import urllib
from datetime import datetime

import dateutil.relativedelta


logger = logging.getLogger(__name__)


@login_required(login_url='login')
def home(request):
    user = request.user
    student = Student.objects.filter(user=user).first()

    if user.is_staff or user.is_superuser:
        return HttpResponseRedirect(reverse('admin:index'))

    form = EnrollForm()
    if request.method == "POST":
        form = EnrollForm(request.POST)

        if form.is_valid():
            secret_key = form.cleaned_data['secret_key']

            course = Course.objects.filter(enroll_key=secret_key).first()
            if course:
                already_registered = Student.objects.filter(pk=student.id, courses__id=course.id).exists()
                if already_registered:
                    messages.warning(request, 'You have already registered that course')
                else:
                    student.courses.add(course)
                    student.save()
                    messages.success(request, 'You are successfully registered to the course')

            else:
                form.add_error('secret_key', "Invalid Secret Key")
            return redirect('home')

    errors = form.errors or None
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
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            student = Student.objects.create(user=user)
            student.save()
            current_site = get_current_site(request)
            subject = 'Activate Your FAST AutoGrader Account'
            message = render_to_string('account/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('account_activation_sent')

            #user = form.save()
            #user.refresh_from_db()
            #user.save()

            #student = Student.objects.create(user=user)
            #student.save()

            #raw_password = form.cleaned_data.get('password1')
            #user = authenticate(username=user.username, password=raw_password)
            #login(request, user)
            #request.session['username'] = user.username
            #return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.student.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'account/account_activation_invalid.html')


def account_activation_sent(request):
    return render(request, 'account/account_activation_sent.html')

def download(request):
    # TODO: break when user try to download Instructor Test file
    submission_id = request.GET.get('sid')
    assignment_id = request.GET.get('aid')
    raw = request.GET.get('raw')
    action = request.GET.get('action')

    # Check
    if assignment_id:
        assignment = Assignment.objects.filter(id=assignment_id)
        if assignment.exists():
            assignment = assignment.first()
            if action == "student_test":
                path = assignment.student_test.url
            elif action == "zip_file":
                path = os.path.dirname(assignment.student_test.url) + "/assignment" + assignment_id + ".zip"
            elif action == "config_file":
                path = os.path.dirname(assignment.student_test.url) + "/config.json"
            elif action == "assignment_file":
                path = assignment.assignment_file.url
            else:
                return Http404
    elif submission_id:
        submission = Submission.objects.get(id=submission_id)
        # Download modifiable_file of student when user is staff or admin
        if submission and action == "modifiable_file" and (request.user.is_staff or request.user.is_superuser):
            path = submission.get_modifiable_file()
        elif submission:
            path = submission.get_log_file()

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            if raw:
                try:
                    url = urllib.request.pathname2url(file_path)
                except AttributeError:
                    # fix for python2 compatability idiocy
                    url = urllib.pathname2url(file_path)

                content_type = mimetypes.guess_type(url)[0]
                if not content_type:
                    content_type = "text/plain"
            else:
                content_type = 'application/force-download'
            response = HttpResponse(fh.read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response

    raise Http404


@login_required(login_url='login')
def course(request, course_id, assignment_id=0):
    user = User.objects.get(pk=request.user.id)
    student = Student.objects.filter(user=user, courses=course_id).first()

    if not student:
        return redirect("home");

    course = Course.objects.get(id=course_id)

    assignments = Assignment.objects.filter(course=course, open_date__lte=timezone.now())

    selected_assignment = None
    submission_history = None
    assignment_zip_file = None
    time_left = ''
    modifiable_filename = None
    expired = False

    if (assignment_id != 0):
        selected_assignment = Assignment.objects.get(id=assignment_id, open_date__lte=timezone.now())
        submission_history = Submission.objects.filter(student=student,assignment=selected_assignment).order_by("-publish_date")
        assignment_zip_file = os.path.split(selected_assignment.student_test.url)[0] + "/assignment" + str(assignment_id) + ".zip"
        due_date = selected_assignment.due_date
        now_time = timezone.now()



        if due_date > now_time:
            rd = dateutil.relativedelta.relativedelta (due_date, now_time)
            time_left = "%d days, %d hours and %d minutes" % (rd.days, rd.hours, rd.minutes) + " left"
        else:
            time_left = "Submission date has passed!"
            expired = True

        # only one assignment file for now
        modifiable_filename = os.path.basename(selected_assignment.assignment_file.url)

    return render(request, 'course.html', {
            'assignment_zip_file': assignment_zip_file,
            'assignment_id': int(assignment_id),
            'course': course,
            'assignments': assignments,
            'selected_assignment': selected_assignment,
            'submission_history': submission_history,
            'time_left' : time_left,
            'modifiable_filename': modifiable_filename,
            'assignment_expired': expired
        }
    )


@csrf_exempt
def api(request, action):
    email = request.POST.get('email')
    submission_pass = request.POST.get('submission_pass')

    student = Student.objects.filter(user__email=email, submission_pass=submission_pass)
    if (student.exists()):
        student = student[0]
        if (action == "submit_assignment"):

            if request.method == 'POST':

                assignment = Assignment.objects.filter(id=request.POST.get('assignment'), open_date__lte=timezone.now()).first()

                if not assignment:
                    response_data = {"status": 404, "type": "ERROR",
                     "message": "Assignment doesn't exists"}
                elif assignment and timezone.now() > assignment.due_date:
                    response_data = {"status": 400, "type": "ERROR",
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

                    # Move Student Test File
                    shutil.copy(assignment.student_test.url, extract_directory)
    
                    score, outlog = run_student_tests(extract_directory, assignment.total_points, assignment.timeout)
                    
                    submission.passed  = score[0]
                    submission.failed  = score[1]
                    
                    submission.save()

                    response_data = {"status": 200, "type": "SUCCESS",
                         "message": [score[0], score[1], submission.get_score()]}

            else:
                response_data = {"status": 400, "type": "ERROR",
                         "message": "Use POST method"}
        else:
            response_data = {"status": 400, "type": "ERROR",
                         "message": "Invalid action"}
    else:
        response_data = {"status": 403, "type": "ERROR",
                         "message": "Invalid student"}

    r = JsonResponse(response_data, safe=False)
    r.status_code = response_data['status']
    return r

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('/autograde')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {
        'form': form
    })

@staff_member_required
def assignment_report(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    submissions = assignment.get_student_latest_submissions()
    return render(request, 'admin/assignment_report.html', {
        'submissions': submissions,
        'assignment': assignment,
        'generated_on': timezone.now()
    })

