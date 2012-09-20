from django import forms
from django.contrib.auth.models import User
from accounts.models import *

class NewUserForm(forms.ModelForm):
  password = forms.CharField(widget=forms.PasswordInput(render_value=False))
  password2 = forms.CharField(widget=forms.PasswordInput(render_value=False))
  email = forms.EmailField(required=True)
  
  class Meta:
    model = User
    fields = [
      'username',
      'password',
      'email',
    ]
  
  def clean_email(self):
    email = self.cleaned_data['email'].strip()
    users = User.objects.filter(email=email)
    if len(users) != 0:
      raise forms.ValidationError('This email address already has an account. (Only one account is allowed per email address)')
    return email

  def clean_password(self):
    password = self.cleaned_data['password']
    return password
  
  def clean_password2(self):
    password2 = self.cleaned_data['password2']
    if self.is_valid():
      password = self.cleaned_data['password']
      if str(password) != str(password2):
        raise forms.ValidationError('Passwords do not match')
    return password2
  
class PreferencesForm(forms.ModelForm):
  class Meta:
    model = Settings
    fields = [
      'dailyTestMaxItems',
      'receiveEmail'
    ]