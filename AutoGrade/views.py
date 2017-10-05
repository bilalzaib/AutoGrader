from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, authenticate, logout
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
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Student, Course, Assignment, Submission
from .forms import SignUpForm, EnrollForm, ChangeEmailForm
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

    # If user is student and also staff member then allow him the access to student panel.
    if not student and (user.is_staff or user.is_superuser):
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
                messages.error(request, 'Invalid Enroll Key')
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

            """
            try:
                user.email_user(subject, message)
                return redirect('account_activation_sent')
            except Exception:
                form.add_error(None, "Email sending failed, try again later.")
                user.delete()
            """


            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            request.session['username'] = user.username
            return redirect('home')
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

@login_required(login_url='login')
def download(request):
    # TODO: break when user try to download Instructor Test file
    submission_id = request.GET.get('sid')
    assignment_id = request.GET.get('aid')
    raw = request.GET.get('raw')
    action = request.GET.get('action')

    # Check
    if assignment_id:
        student = Student.objects.get(user=request.user);
        assignment = Assignment.objects.filter(id=assignment_id, course__in=student.courses.all(), open_date__lte=timezone.now()).distinct()
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
        else:
            path = ""
    elif submission_id:
        submission = Submission.objects.get(id=submission_id)
        
        # Download modifiable_file of student when user is staff or admin
        if submission and action == "modifiable_file" and (request.user.is_staff or request.user.is_superuser):
            path = submission.get_modifiable_file()
        elif submission and settings.ALLOW_INSTRUCTOR_TEST_LOG_VIEW:
            path = submission.get_log_file()
        else:
            path = ""
    else:
    	path = ""

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

    assignments = Assignment.objects.filter(course=course, open_date__lte=timezone.now()).order_by('due_date')

    selected_assignment = None
    submission_history = None
    assignment_zip_file = None
    time_left = ''
    modifiable_filename = None
    expired = False

    late_days_left = student.get_late_days_left(course)

    try:
        show_view_log_button = settings.ALLOW_INSTRUCTOR_TEST_LOG_VIEW
    except AttributeError:
        show_view_log_button = True

    if (assignment_id != 0):
        try:
            selected_assignment = Assignment.objects.get(id=assignment_id, open_date__lte=timezone.now())
        except ObjectDoesNotExist:
            raise Http404;

        submission_history = Submission.objects.filter(student=student,assignment=selected_assignment).order_by("-publish_date")
        assignment_zip_file = os.path.split(selected_assignment.student_test.url)[0] + "/assignment" + str(assignment_id) + ".zip"
        due_date = selected_assignment.corrected_due_date(student)

        now_time = timezone.now()

        if due_date > now_time:
            rd = dateutil.relativedelta.relativedelta (due_date, now_time)
            time_left = "%d days, %d hours and %d minutes" % (rd.days, rd.hours, rd.minutes) + " left"
        else:
            time_left = "Submission date has passed!"
            expired = True

        # only one assignment file for now
        modifiable_filename = os.path.basename(selected_assignment.assignment_file.url)

    else:
        due_date = None # no assignment therefore no due date

    return render(request, 'course.html', {
            'assignment_zip_file': assignment_zip_file,
            'corrected_due_date': due_date,
            'late_days_left': late_days_left,
            'assignment_id': int(assignment_id),
            'course': course,
            'assignments': assignments,
            'show_view_log_button': show_view_log_button,
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
    if student.exists():
        student = student[0]
        if student.user.is_active == False:
            response_data = {"status": 400, "type": "ERROR",
                         "message": "Verify your email first."}
        elif (action == "submit_assignment"):

            if request.method == 'POST':

                assignment = Assignment.objects.filter(id=request.POST.get('assignment'), course__in=student.courses.all(), open_date__lte=timezone.now()).distinct().first()

                if not assignment:
                    response_data = {"status": 404, "type": "ERROR",
                     "message": "Assignment doesn't exists"}
                elif assignment and timezone.now() > assignment.corrected_due_date(student):
                    response_data = {"status": 400, "type": "ERROR",
                     "message": "Assignment submission date expired. You may be able to request an extension from the web interface."}
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

@login_required
def resend_signup_email(request):
    user = request.user

    current_site = get_current_site(request)
    subject = 'Activate Your FAST AutoGrader Account'
    message = render_to_string('account/account_activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })

    user.email_user(subject, message)
    messages.success(request, 'Verification email sent, check your email account.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def change_email(request):
    email = request.POST.get("email")

    form = ChangeEmailForm(request.POST)
    if form.is_valid():
        user = request.user
        user.email = form.cleaned_data.get('email')
        user.save()

        current_site = get_current_site(request)
        subject = 'Activate Your FAST AutoGrader Account'
        message = render_to_string('account/account_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })

        user.email_user(subject, message)
        messages.success(request, 'Email updated and verification email sent.')
    else:
        for field in form:
            for error in field.errors:
                messages.warning(request, field.label + ": " + error)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@staff_member_required
def assignment_report(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    submissions = assignment.get_student_and_latest_submissions()
    return render(request, 'admin/assignment_report.html', {
        'submissions': submissions,
        'assignment': assignment,
        'generated_on': timezone.now()
    })

@staff_member_required
def moss_submit(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    assignment.moss_submit() # This will enable the view button if report is generated
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@staff_member_required
def moss_view(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    file_path = os.path.join(settings.MEDIA_ROOT, assignment.moss_report())
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            content_type = 'text/html'
            response = HttpResponse(fh.read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response

    raise Http404

@staff_member_required
def assignment_aggregate_report(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    submissions = assignment.get_student_and_latest_submissions()

    all_submissions = {}
    for submission, student in submissions:
        if submission:
            file_path = submission.get_modifiable_file()
            file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            with open(file_path, 'rb') as fh:
                submission_content = fh.read()
                submission.file_content = submission_content

    return render(request, 'admin/assignment_aggregate_report.html', {
        'submissions': submissions,
        'assignment': assignment,
        'generated_on': timezone.now()
    })

@staff_member_required
def loginas(request, student_id):
    # Save staff id so when student account logout so that staff is logged in
    staff_user_id = request.user.id

    student = Student.objects.get(id=student_id)
    user = student.user
    login(request, student.user)
    request.session['username'] = user.username

    request.session['staff_loginas'] = True
    request.session['staff_loginas_referer'] = request.META.get('HTTP_REFERER')
    request.session['staff_loginas_userid'] = staff_user_id

    return redirect('home')

def logout_student(request):
    if "staff_loginas" in request.session and request.session['staff_loginas']:
        staff_user_id = request.session['staff_loginas_userid']
        loginas_referer = request.session['staff_loginas_referer']
        login(request, User.objects.get(id=staff_user_id))
        return HttpResponseRedirect(loginas_referer)
    else:
        logout(request)
        return redirect('login')
