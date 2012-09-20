from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('exporting.views',
  ('csv', 'csv'),
)