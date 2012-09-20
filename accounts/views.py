from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template  import RequestContext
from django.core.mail import send_mail
from djangoappengine.utils import on_production_server
import datetime, hashlib, random
from accounts.forms import *

# ---- Account Creation -------------------------------------------------
KEY_EXPIRATION_DELTA = datetime.timedelta(days=2)

def buildActivationKey(username, email):
  salt = hashlib.sha224(str(random.random())).hexdigest()[:5]
  activationKey = hashlib.sha224(salt+username+email).hexdigest()
  keyExpires = datetime.datetime.today() + KEY_EXPIRATION_DELTA
  return (activationKey, keyExpires)

def newUser(request):
  if request.user.is_authenticated():
    return HttpResponseRedirect('/') # this user already is logged in - redirect to home
  if request.method == 'POST':
    newUserForm = NewUserForm(request.POST)
    if newUserForm.is_valid():
      # build the user
      user = newUserForm.save(commit=False)
      user.is_active = False
      if not on_production_server:
        user.is_active = True
        user.is_superuser = True
        user.is_staff=True
      user.set_password(newUserForm.cleaned_data['password'])

      # Build the activation key for this account
      (activationKey, keyExpires) = buildActivationKey(user.username, user.email)

      # save the user's Settings
      user.save()
      settings = Settings(user=user, joined=datetime.datetime.today(), activationKey=activationKey, keyExpires=keyExpires)
      settings.save()

      # send an email with the confirmation link
      email_subject = "New Account Confirmation"
      email_body = "WELCOME MESSAGE \
                   \n\n To Activate your account, go to the following address within 48 hours: \
                   \n\n http://www.thoughtsaver0.appspot.com/accounts/newUser/activate/%s" % (
                      settings.activationKey)
      send_mail(email_subject, email_body, 'accounts@thoughtsaver0.appspotmail.com', [user.email], fail_silently=True)
      return render_to_response('accounts/newuser_complete.html', {'success': True})
  else:
    newUserForm = NewUserForm()
  return render_to_response('accounts/newUser.html', {'newUserForm': newUserForm}, context_instance=RequestContext(request))
  
def activateAccount(request, activationKey):
  if request.user.is_authenticated():
    return HttpResponseRedirect('/')
  settings = Settings.objects.filter(activationKey=activationKey)
  if len(settings) == 0:
    return render_to_response('accounts/confirmActivation.html', {'success': False})
  settings = settings[0]
  if settings.user.is_active:
    return HttpResponseRedirect('/')
  if settings.keyExpires < datetime.datetime.today():
    return render_to_response('accounts/confirmActivation.html', {'expired': True})
  user_account = settings.user
  user_account.is_active = True
  user_account.save()
  return render_to_response('accounts/confirmActivation.html', {'success': True}, context_instance=RequestContext(request))

def home(request):
  if request.user.is_authenticated() == True:
    return HttpResponseRedirect('/myCards')
  return render_to_response('accounts/home.html', context_instance=RequestContext(request))
  
#TODO @login_required
def preferences(request):
  saved = False
  settings = request.user.get_profile()
  if request.method == 'POST':
    preferencesForm = PreferencesForm(request.POST)
    if preferencesForm.is_valid():
      receiveEmail = preferencesForm.cleaned_data['receiveEmail']
      dailyTestMaxItems = preferencesForm.cleaned_data['dailyTestMaxItems']
      settings.dailyTestMaxItems = dailyTestMaxItems
      settings.receiveEmail = receiveEmail
      settings.save()
      saved = True
  else:
    preferencesForm = PreferencesForm(instance=settings)
  return render_to_response('accounts/preferences.html', {
    'preferencesForm': preferencesForm,
    'saved': saved,
  }, context_instance=RequestContext(request))