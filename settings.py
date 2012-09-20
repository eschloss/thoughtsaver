# Initialize App Engine and import the default settings (DB backend, etc.).
# If you want to use a different backend you have to remove all occurences
# of "djangoappengine" from this file.
from djangoappengine.settings_base import *
DATABASES['default']['HIGH_REPLICATION'] = True

import os
from djangoappengine.utils import on_production_server, have_appserver

DEBUG = not on_production_server
ADMINS = (
    ('Eric', 'orpheuskl@gmail.com'),  
)
DEFAULT_FROM_EMAIL = 'accounts@thoughtsaver.com'
SERVER_EMAIL = 'accounts@thoughsaver.com'

# Login and Logout default pages
LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/'

# Define user profile associated with a User
AUTH_PROFILE_MODULE = 'accounts.Settings'

TIME_ZONE = 'UTC'

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440 # 2.5 MB

SECRET_KEY = 'skjhs2aiufa21435uhifshvsbhfi27623#4a42dhyiuf2134ssghih'

# Media generator stuff
MEDIA_DEV_MODE = False
DEV_MEDIA_URL = '/devmedia/'
PRODUCTION_MEDIA_URL = '/media/'
GLOBAL_MEDIA_DIRS = (os.path.join(os.path.dirname(__file__), 'site_media'),)
MEDIA_BUNDLES = (
    ('main.js',
     'js-libraries/jqueryui/js/jquery-1.6.2.min.js',
     'js-libraries/jqueryui/js/jquery-ui-1.8.16.custom.min.js',
     ),
    ('test.js', 'js/test.js'),
    ('myCards.js', 'js/myCards.js'),
    ('bookmarklet.js', 'js/bookmarklet.js'),
    ('myTags.js', 'js/myTags.js'),
    ('myGoogleDocs.js', 'js/myGoogleDocs.js'),
    ('myCards.css', 'css/myCards.css'),
    ('header.css', 'css/header.css'),
    ('myTags.css', 'css/myTags.css'),
    ('base.css', 'css/base.css'),
    ('bookmarklet.css', 'css/bookmarklet.css'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'djangotoolbox',
    'autoload',
    'dbindexer',
    'bs4',
    'mediagenerator',
    'atom',
    'gdata',
    'accounts',
    'flashcards',
    'mailhandler',
    'importing',
    'exporting',

    # djangoappengine should come last, so it can override a few manage.py commands
    'djangoappengine',
)

MIDDLEWARE_CLASSES = (
    'mediagenerator.middleware.MediaMiddleware', #must be first
    #'django.middleware.cache.UpdateCacheMiddleware', #activate later
    #'django.middleware.gzip.GZipMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',#TODO activate csrf tokens
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware', # doing anything?
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
)

# This test runner captures stdout and associates tracebacks with their
# corresponding output. Helps a lot with print-debugging.
TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

ROOT_URLCONF = 'urls'


# not necessary
'''
# Activate django-dbindexer if available
try:
    import dbindexer
    DATABASES['default']['HIGH_REPLICATION'] = True
    DATABASES['native'] = DATABASES['default']
    DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
    INSTALLED_APPS += ('dbindexer',)
    DBINDEXER_SITECONF = 'dbindexes'
    MIDDLEWARE_CLASSES = ('dbindexer.middleware.DBIndexerMiddleware',) + \
                         MIDDLEWARE_CLASSES
except ImportError:
    pass
'''