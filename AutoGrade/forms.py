from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Section

class SignUpForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email' , 'password1', 'password2', )

class EnrollForm(forms.Form):
    section = forms.ModelChoiceField(queryset=Section.objects.all().order_by('sec_name'))

    class Meta:
        fields = ('Section')