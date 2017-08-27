from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from .models import Course, Submission, Assignment

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email' , 'password1', 'password2', )

class EnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all().order_by('name'))
    secret_key = forms.CharField(
    	widget=forms.TextInput(attrs={'placeholder': 'ABCXYZ12'}),
    	label='Secret Key', 
    	required=False)

    class Meta:
        fields = ('course', 'secret_key')
