from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from .models import Course, Submission, Assignment

class SignUpForm(UserCreationForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'Email addresses must be unique.')
        return email

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email' , 'password1', 'password2', )

class EnrollForm(forms.Form):
    secret_key = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'ABCXYZ12'}),
        label='Secret Key', 
        required=False)

    class Meta:
        fields = ('secret_key')

class ChangeEmailForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(u'That email is already used.')
        return email

    class Meta:
        fields = ('email')

