from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('importing.views',
  ('myGoogleDocs$', 'myGoogleDocs'),
  ('importingOptions$', 'importingOptions'),
  ('csv$', 'csv'),
  (r'^get_oauth_token', 'get_oauth_token'),
  (r'^get_access_token', 'get_access_token'),
  (r'^choose_fields/([^/]*)/([^/]*)', 'choose_fields'),
  (r'^generate_cards/([^/]*)/([^/]*)', 'generate_cards'),
  (r'^import_spreadsheet/([^/]*)/([^/]*)/([^/]*)/(.*)', 'import_spreadsheet'),
  (r'^select_worksheet/([^/]*)/(.*)', 'select_worksheet'),
)