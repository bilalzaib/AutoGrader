from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import Student,Section,Assignment
from .forms import SignUpForm,EnrollForm

@login_required(login_url = 'login')
def home(request):
    return render(request, 'home.html', {'sections' : Section.objects.all()})

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
            return redirect('enroll')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def enroll(request):
   form = EnrollForm()
   if request.method == "POST":
      form = EnrollForm(request.POST)
      if form.is_valid():
          sec = form.cleaned_data['section']
          usern = request.session.get('username', None)
          u = User.objects.get(username = usern)
          s = Student.objects.get(user=u)
          s.section = sec
          s.save()
         #redirect to the url where you'll process the input
          return redirect('home')
   errors = form.errors or None # form not submitted or it has errors
   return render(request, 'enroll.html',{
          'form': form,
          'errors': errors,
   })

def section(request,section_id):
    sec = Section.objects.get(id = section_id)
    return render(request, 'section.html', {'assignments' : Assignment.objects.filter(section = sec), 'section' : sec})

def assignment(request,assignment_id):
    assignment = Assignment.objects.get(id = assignment_id)
    return render(request, 'assignment.html', {'assignment' : assignment})