from flaskext.uploads import UploadSet, IMAGES

SITE_TITLE = 'Hangspot'
SITE_TAG_LINE = 'Where people meet each other.'
DEBUG = True
SECRET_KEY = "secret key"
SQLALCHEMY_DATABASE_URI = 'postgres://hangspot_user:Cl0ck$@localhost:5432/hangspot'
SQLALCHEMY_ECHO = False
RECAPTCHA_PUBLIC_KEY  = 'key here'
RECAPTCHA_PRIVATE_KEY = 'pass here'
RECAPTCHA_OPTIONS = {
    'theme': 'white',
    'lang': 'en',
    'tabindex': 2,
}


MIN_AGE = 17
DAYS_IN_YEAR = 365.25

UPLOADED_PHOTOS_DEST = '/home/hangspot_user/hangspot/static/photos/'
UPLOADED_PHOTOS_URL = '/static/photos/'

PHOTO_UPLOAD_SET = UploadSet('photos', IMAGES)
LOG_FILE = '/tmp/flask-hangspot.log'
LOCALE = 'en'
