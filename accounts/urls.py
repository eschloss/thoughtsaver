from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('accounts.views',
  (r'^newUser$', 'newUser'),
  (r'^newUser/activate/(?P<activationKey>.+)$', 'activateAccount'),
  (r'^preferences$', 'preferences'),
  #(r'^forgotPassword$', 'forgotPassword'),
  #(r'^resetPassword/(?P<activationKey>.+)$', 'resetPassword'),
)