from flaskext import wtf 
from pyzipcode import ZipCodeDatabase
from datetime import datetime
from settings import MIN_AGE, PHOTO_UPLOAD_SET
from models import User

zip_code_db = ZipCodeDatabase()

empty_choice = [('','--')]
months = [('','Month')] + zip(
                              map(unicode, xrange(1,13)),
                              ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                          )
days = [('','Day')] + [(d, d) for d in map(unicode, xrange(1,32))]
years = [('','Year')]  + [(y, y) for y in map(unicode, xrange(datetime.now().year - MIN_AGE, 1900, -1))]
genders = [('','--')] + [('M', 'Male'), ('F', 'Female')]

min_ages = [(0, '--')] + [(a, a) for a in xrange(MIN_AGE,100)]
max_ages = [(0, '--')] + [(a, a) for a in xrange(MIN_AGE,100)]
sort_types = [('last_login DESC','Last Login'), 
              ('birth_date DESC','Age')]  # TODO ADD status

class BrowseForm(wtf.Form):
    min_age = wtf.SelectField(choices=min_ages, coerce=int)
    max_age = wtf.SelectField(choices=max_ages, coerce=int)
    gender = wtf.SelectField(choices=genders)
    sort_by = wtf.SelectField(choices=sort_types)

class SignUpForm(wtf.Form):
    username = wtf.TextField( validators=[wtf.Required(), wtf.Length(min=4, max=16)])
    password = wtf.PasswordField( validators=[wtf.Required(), wtf.Length(min=6,max=16)])
    email = wtf.TextField(validators=[wtf.Email()])
    birth_month = wtf.SelectField(choices=months, validators=[wtf.Required()])
    birth_day = wtf.SelectField(choices=days, validators=[wtf.Required()])
    birth_year = wtf.SelectField(choices=years, validators=[wtf.Required()])
    gender = wtf.SelectField( choices=genders, validators=[wtf.Required()])
    zip_code = wtf.TextField( validators=[wtf.Required()])
    agree_terms = wtf.BooleanField('I agree to terms of use', validators=[wtf.Required()])
    recaptcha = wtf.RecaptchaField('Human Test')

    def validate_username(form, field):
        if field.data and User.get_user(field.data):
            raise wtf.ValidationError('Usename already exists.')

    def validate_zip_code(form, field):
        try:
            zip_code_db[field.data]
        except IndexError:
            raise wtf.ValidationError('Invalid zip code.')

class LoginForm(wtf.Form):
    username = wtf.TextField(validators=[wtf.Required()])
    password = wtf.PasswordField(validators=[wtf.Required()])
    remember_me = wtf.BooleanField()

class SubmitForm(wtf.Form):
    submit = wtf.SubmitField()

class CommentForm(wtf.Form):
    comment = wtf.TextAreaField(validators=[wtf.Required()])
    
class PrivateMessageForm(wtf.Form):
    subject = wtf.TextField(validators=[wtf.Required()])
    message = wtf.TextAreaField(validators=[wtf.Required()])

class PhotoForm(wtf.Form):
    photo = wtf.FileField("Add a photo",
                       validators=[wtf.file_required(),
                       wtf.file_allowed(PHOTO_UPLOAD_SET, "Images only!")])

class FeedbackForm(wtf.Form):
    name = wtf.TextField(validators=[wtf.Required()])
    email = wtf.TextField(validators=[wtf.Email()])
    message = wtf.TextAreaField(validators=[wtf.Required()])
    recaptcha = wtf.RecaptchaField('Human Test')
