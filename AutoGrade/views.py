from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User

from .models import Student, Course, Assignment, Submission
from .forms import SignUpForm, EnrollForm

@login_required(login_url = 'login')
def home(request):
    user = User.objects.get(pk=request.user.id)
    student = Student.objects.filter(user=user)[0]
    print (student)
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

def section(request,section_id):
    sec = Section.objects.get(id = section_id)
    return render(request, 'section.html', {'assignments' : Assignment.objects.filter(section = sec), 'section' : sec})

def assignment(request,assignment_id):
    assignment = Assignment.objects.get(id = assignment_id)
    return render(request, 'assignment.html', {'assignment' : assignment})

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