from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers

from .models import Student, Course, Assignment, Submission
from .forms import SignUpForm, EnrollForm

from django.http import JsonResponse

import json

@login_required(login_url = 'login')
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
          redirect('home');

    errors = form.errors or None
    print (student.courses.all())
    return render( request, 
      'home.html', 
      { 
        'courses' : student.courses.all(),
        'form'    : form, 
        'errors'  : errors,
        'student' : student
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

@login_required(login_url = 'login')
def course(request, course_id, assignment_id = 0):
    user = User.objects.get(pk=request.user.id)
    student = Student.objects.filter(user=user)[0]
    course = Course.objects.get(pk=course_id)
    assignments = Assignment.objects.filter(course=course)

    selected_assignment = None
    submission_history = None
    if (assignment_id != 0) :
      selected_assignment = Assignment.objects.get(id=assignment_id)
      submission_history = Submission.objects.filter(student=student)

    return render(request, 'course.html', {
        'assignment_id'       : int(assignment_id),
        'course'              : course, 
        'assignments'         : assignments, 
        'selected_assignment' : selected_assignment,
        'submission_history'  : submission_history
      }
    )

@csrf_exempt
def api(request, action):
  email = request.POST.get('email')
  submission_pass = request.POST.get('submission_pass')

  user = User.objects.filter(email=email)
  if (user):
    student = Student.objects.filter(user=user[0], submission_pass=submission_pass)[0]
    
    if (student):
      if (action == "get_course"):
        courses = []
        for course in student.courses.all():
          courses.append(course.name)
        response_data = {"status": 200, "type": "SUCCESS", "data": courses}
      elif (action == "get_assignment"):
        course_id = request.POST.get('course_id')
        courses = Course.objects.filter(course_id=course_id)

        assignments = []
        for assignment in Assignment.objects.filter(course=course):
          assignments.append(assignment.title)

        response_data = {"status": 200, "type": "SUCCESS", "data": assignments}
      elif (action == "submit_assignment"):
        pass
    else:
      response_data = {"status": 400, "type": "ERROR", "message": "Invalid Student"}
  else :
    response_data = {"status": 400, "type": "ERROR", "message": "Invalid User"}


  return JsonResponse(response_data)