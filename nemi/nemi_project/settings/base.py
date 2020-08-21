import os
import sys

import dj_database_url


PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE_HOME = os.path.split(PROJECT_HOME)[0]

DEBUG = False

ADMINS = (
    ('Mary Bucknell', 'mbucknell@usgs.gov'),
    ('Daniel Naab', 'dnaab@usgs.gov'),
)
MANAGERS = ADMINS

# Set `SECRET_KEY` environment variable or set in `local.py`
SECRET_KEY = os.environ.get('SECRET_KEY')

# This checks to see if django tests are running (i.e. manage.py test)
RUNNING_TESTS = sys.argv and 'test' in sys.argv

if RUNNING_TESTS:
    DB_ENGINE = 'django.db.backends.sqlite3'
else:
    DB_ENGINE = 'django.db.backends.oracle'

# Set `DATABASE_URL` in environment or override in `local.py`.
DATABASES = {
    'default': dj_database_url.config() or {
        'ENGINE': DB_ENGINE,
        'NAME': 'sqlite.db'
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

TEST_RUNNER = 'nemi_project.test_runner.ManagedModelTestRunner'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(SITE_HOME, '../static/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    (os.path.join(PROJECT_HOME, 'static'),)
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'nemi_project.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'nemi_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_HOME, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'common.context_processors.project_settings',
            ],
            'debug': [
                DEBUG,
            ],
        },
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django.contrib.flatpages',
    'django.forms',

    # Third party apps
    'django_object_actions',
    'rest_framework',
    'tinymce',

    # NEMI/CIDA specific apps
    'common',
    'newsfeed',
    'domhelp',
    'methods',
    'protocols',
    'sams',
    'reference',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

SESSION_COOKIE_AGE = 28800  # In seconds, this is eight hours

# NEMI specific setting. List of emails to send new account notifications to.
NEW_ACCOUNT_NOTIFICATIONS = ADMINS

# Water Quality Portal URL
WQP_URL = "http://www.waterqualitydata.us"

# Code to be used for google analytics. If tracking is desired for a server,
# set to the track code in local.py.
GA_TRACKING_CODE = None

# Set security based on whether DEBUG is on
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Set up TinyMCE configuration
TINYMCE_JS_URL = STATIC_URL + 'tiny_mce/tiny_mce.min.js'

TINYMCE_DEFAULT_CONFIG = {
    'theme' : "advanced",
}

if os.getenv('JENKINS_URL', False):
    JENKINS_TEST_RUNNER = 'nemi_project.test_runner.JenkinsManagedModelTestRunner'
    INSTALLED_APPS += ('django_jenkins',)
    PROJECT_APPS = (
        'common',
        'methods',
        'protocols',
        'sams',
        'newsfeed',
        'domhelp',
    )
    DATABASES['default'].update({
        'ENGINE': os.getenv('DBA_SQL_DJANGO_ENGINE'),
        'USER': os.getenv('DBA_SQL_ADMIN'),
        'PASSWORD': os.getenv('DBA_SQL_ADMIN_PASSWORD'),
        'HOST': os.getenv('DBA_SQL_HOST'),
        'PORT': os.getenv('DBA_SQL_PORT')
    })

def show_debug_toolbar(settings):
    settings['MIDDLEWARE'] += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

    settings['DEBUG_TOOLBAR_PANELS'] = (
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    )

    settings['DEBUG_TOOLBAR_CONFIG'] = {
        'INTERCEPT_REDIRECTS': False,
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'HIDE_DJANGO_SQL': False,
        'TAG': 'div',
    }

    settings['INSTALLED_APPS'] += ('debug_toolbar',)


# If we are running the test suite, disable migrations. This avoids problems
# caused by switching previously-unmanaged models to managed ones.
if any(arg in ('test', 'jenkins') for arg in sys.argv[1:]):
    class DisableMigrations(object):
        def __contains__(self, item):
            return True
        def __getitem__(self, item):
            return None

    MIGRATION_MODULES = DisableMigrations()
