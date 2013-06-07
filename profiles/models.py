from flaskext.sqlalchemy import SQLAlchemy
from flask import Flask, session
from werkzeug import generate_password_hash, check_password_hash
from datetime import datetime, date
from pyzipcode import ZipCodeDatabase
from settings import DAYS_IN_YEAR, PHOTO_UPLOAD_SET

zip_code_db = ZipCodeDatabase()
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    __mapper_args__ = dict(order_by='last_login DESC')

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(64))
    email = db.Column(db.String(320))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(1))
    zip_code = db.Column(db.String(5))
    date_joined = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, default=datetime.now)
    
    # Relations
    interview_answers = db.relation('InterviewAnswer')
    comments_received = db.relation('Comment', primaryjoin='User.id==Comment.user_id', backref="receiver")
    comments_sent = db.relation('Comment', primaryjoin='User.id==Comment.commenter_id', backref="sender")
    visits = db.relation('Visit', primaryjoin='User.id==Visit.user_id')
    buddies = db.relation('Buddy', primaryjoin='User.id==Buddy.user_id')
    photos = db.relation('Photo', primaryjoin="User.id==Photo.user_id", backref="user")

    def __init__(self, data):
        self.username = data['username']
        self.set_password(data['password'])
        self.email = data['email']
        self.birth_date = datetime(int(data['birth_year']), 
                                   int(data['birth_month']),
                                   int(data['birth_day']))
        self.gender = data['gender']
        self.zip_code = data['zip_code']
        self.date_joined = self.last_login = datetime.now()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def age(self):
        return int((date.today() - self.birth_date).days/DAYS_IN_YEAR)

    def photo(self):
        if self.photos:
            return self.photos[0].url()

        return {'M':'/static/images/male.jpeg',
                'F': '/static/images/female.jpeg'}[self.gender]

    def location(self):
        z = zip_code_db[self.zip_code]
        return "%s" % (z.state)

    def asl(self):
        return '%s/%s/%s' % (self.age(), self.gender, self.location())
      
    @classmethod
    def get_user(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_current_user(cls):
        if 'username' in session:
            return cls.get_user(session['username'])
        return None

    @classmethod
    def is_authenticated(cls, username=None):
        if 'username' in session:
            return not username or session['username'] == username 
        return False


    @classmethod
    def login(cls, username, password, remember=False):
        user = cls.get_user(username)
        if user and user.check_password(password):
            session['username'] = username
            session.permanent = remember
            return user
        return None

    @classmethod
    def logout(cls):
        session.pop('username', None)


class Photo(db.Model):
    __tablename__ = 'photos'

    def __init__(self, filename, user_id):
        self.filename = filename
        self.user_id = user_id

    def url(self):
        return PHOTO_UPLOAD_SET.url(self.filename)
    def path(self):
        return PHOTO_UPLOAD_SET.path(self.filename)

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

QUESTIONS = {
        1: 'What is your name?',
        2: 'What do you do?',
        3: 'Where are you from?',
        4: 'What is your religion?',
        5: 'Are you single/married/divorced?',
        6: 'What is unique about you?',
        7: 'Got any talents?',
        8: 'What are your pet peeves?',
        9: 'What do you like to do for fun?',
        10: 'Favorite music?',
        11: 'Favorite movies?',
        12: 'Favorite books?',
        13: 'Do you smoke/drink/other?',
        14: 'Tell us about you.',
}

class InterviewAnswer(db.Model):
    __tablename__ = 'interview_answers'
    __mapper_args__ = dict(order_by='question_id')

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    question_id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text)

    def __init__(self, question_id, answer, user_id):
        self.question_id = question_id
        self.answer = answer
        self.user_id = user_id


class Visit(db.Model):
    __tablename__ = 'visits'

    def __init__(self, user_id, visitor_id):
        self.user_id = user_id
        self.visitor_id = visitor_id

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    visitor = db.relation(User, primaryjoin='Visit.visitor_id == User.id')

class Buddy(db.Model):
    __tablename__ = 'buddies'

    def __init__(self, user_id, buddy_id):
        self.user_id = user_id
        self.buddy_id = buddy_id

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    buddy_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    buddy = db.relation(User, primaryjoin='Buddy.buddy_id == User.id')

class Comment(db.Model):
    __tablename__ = 'comments'
    __mapper_args__ = dict(order_by='date_created DESC')

    def __init__(self, user_id, commenter_id, comment):
        self.user_id = user_id
        self.commenter_id = commenter_id
        self.comment = comment


    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    commenter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.now)

class PrivateMessage(db.Model):
    __tablename__ = 'private_messages'
    __mapper_args__ = dict(order_by='date_created DESC')

    def __init__(self, receiver_id, sender_id, subject, message):
        self.receiver_id = receiver_id
        self.sender_id = sender_id
        self.subject = subject
        self.message = message


    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver = db.relation('User', primaryjoin='PrivateMessage.receiver_id == User.id', backref='private_messages')
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender = db.relation('User', primaryjoin='PrivateMessage.sender_id == User.id')
    subject = db.Column(db.String)
    message = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.now)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    __mapper_args__ = dict(order_by='date_created DESC')

    def __init__(self, name, email, message):
        self.name = name
        self.email = email
        self.message = message


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    message = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.now)

