from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

import search
search.autodiscover()

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    ('^_ah/warmup$', 'djangoappengine.views.warmup'),
    #(r'^login/$', 'django.contrib.auth.views.login'),
    #(r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'accounts/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^accounts/', include('accounts.urls')),
    (r'^import/', include('importing.urls')),
    (r'^export/', include('exporting.urls')),
    (r'^$', 'accounts.views.home'),
    (r'^_ah/mail/in@thoughtsaver0.appspotmail.com$', 'mailhandler.views.emailToCard'), #TODO setup forwarding from custom domain to thoughtsaver0.appspot.com
    (r'^mailhandler/', include('mailhandler.urls')), #TODO should make this url more difficult to guess
    (r'', include('flashcards.urls')),
)
