from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('mailhandler.views',
  (r'^sendDailyTests$', 'sendDailyTests'),
  (r'^sendDailyTest$', 'sendDailyTest')
)