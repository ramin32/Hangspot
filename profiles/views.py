from flask import Module, render_template, request, redirect, url_for, session, flash, g, abort
from forms import LoginForm, SignUpForm, SubmitForm, CommentForm, BrowseForm, PhotoForm, FeedbackForm, PrivateMessageForm
from models import User, InterviewAnswer, QUESTIONS, db, Comment, Visit, Photo, Feedback, Buddy, PrivateMessage
import itertools
import datetime
from settings import DAYS_IN_YEAR, PHOTO_UPLOAD_SET
import os
from itertools import ifilter, izip_longest

profiles_module = Module(__name__)

def group_by(iterable, n):
    return izip_longest(*[iter(iterable)]*n)


@profiles_module.before_request
def before_request():
    g.User = User
    g.user = User.get_current_user()
    g.year = datetime.date.today().year
    g.login_form = LoginForm()
    g.group_by = group_by


@profiles_module.route('/photos/<username>/', methods=['GET', 'POST'])
def photos(username):
    if request.method == 'GET':
        return render_template('photos.html', 
            profile_user=User.get_user(username),
            photo_form=PhotoForm())

    else:
        if not(g.user and g.user.username == username):
                flash("You are not authorized for that action.")
                return redirect('views.profiles')

        photo_form = PhotoForm()

        if photo_form.validate_on_submit():
            filename = PHOTO_UPLOAD_SET.save(photo_form.photo.file)
            photo = Photo(filename, g.user.id)
            db.session.add(photo)
            db.session.commit()
            flash("Photo saved.")
            return redirect(url_for('views.photos', username=g.user.username))
        return render_template('photos.html', 
                profile_user=g.user,
                username=g.user.username,
                photo_form=photo_form)

@profiles_module.route('/profiles/<username>/photos/<int:photo_id>/delete/')
def delete_photo(username, photo_id):
    photo = Photo.query.get_or_404(photo_id)

    if not (g.user and g.user.id == photo.user_id):
        flash('You are not authorized for that action.')
        return redirect(url_for('views.photos', username=username))

    try:
        os.remove(photo.path())
    except OSError:
        pass
    db.session.delete(photo)
    db.session.commit()

    flash('Photo successfully removed.')
    return redirect(url_for('views.photos', username=username))


@profiles_module.route('/login', methods=('POST',))
def login():
    if g.user:
        flash('You have already logged on.')
        return redirect(url_for('views.profiles'))

    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.login(form.username.data, form.password.data, form.remember_me.data)
        if user:
            user.last_login = datetime.datetime.now()
            db.session.merge(user)
            db.session.commit()
            if user:
                flash("You have been logged in.")
                return redirect(url_for('views.profile', username=user.username))

    g.login_error = True
    return profiles() 

@profiles_module.route('/logout')
def logout():
    User.logout()
    flash("You have been logged out.")
    return redirect(url_for('views.profiles'))

def years_ago(years):
    year = datetime.timedelta(days=DAYS_IN_YEAR)
    return datetime.date.today() - (year*years)
    
def filter_profiles(browse_form):
    query = User.query
    if browse_form.min_age.data:
        query = query.filter(User.birth_date <= years_ago(browse_form.min_age.data))
    if browse_form.max_age.data:
        query = query.filter(User.birth_date >= years_ago(browse_form.max_age.data))
    if browse_form.gender.data:
        query = query.filter(User.gender == browse_form.gender.data)
    if browse_form.sort_by.data:
        query = query.order_by(browse_form.sort_by.data)
    return query.all()

@profiles_module.route('/')
def profiles():
    if request.args:
        browse_form=BrowseForm(request.args, csrf_enabled=False)
        if browse_form.validate():
            users = filter_profiles(browse_form)
        else:
            users = User.query.all()
    else:
        browse_form=BrowseForm(csrf_enabled=False)
        users = User.query.all()

    return render_template('profiles.html', 
        users=users,
        browse_form=browse_form)


@profiles_module.route('/profiles/<username>/')
def profile(username):
    profile_user = User.get_user(username)

    if not profile_user:
        abort(404)

    if g.user and g.user.username != profile_user.username:
        visit = Visit(profile_user.id, g.user.id) 
        db.session.merge(visit)
        db.session.commit()

    return render_template('profile.html',
        profile_user=profile_user,
        questions=QUESTIONS,
        comment_form=CommentForm())


@profiles_module.route('/interview/<username>/', methods=('GET', 'POST'))
def interview(username):
    if not User.is_authenticated(username):
        flash("You are not authorized to view that page.")
        return redirect(url_for('views.profiles'))

    user = User.get_user(username)
    if request.method == 'GET':
        answers={a.question_id: a.answer for a in user.interview_answers}
        return render_template('interview.html', 
                               submit_form=SubmitForm(),
                               questions=QUESTIONS,
                               answers=answers)
    elif SubmitForm(request.form).validate_on_submit():
        for a in user.interview_answers:
            db.session.delete(a)
        for (q_id,answer) in request.form.iteritems():
            answer = answer.strip()
            if answer and q_id not in ('csrf', 'submit'):
                a = InterviewAnswer(int(q_id), answer, user.id)
                db.session.add(a)
        db.session.commit()
    return redirect(url_for('views.profile', username=username))
            
@profiles_module.route('/sign_up/', methods=('GET', 'POST'))
def sign_up():
    if g.user:
        flash("You already have an account with us.")
        return redirect(url_for('views.profiles'))

    if request.method == 'GET':
        return render_template('sign_up.html', form=SignUpForm())
    else:
        form=SignUpForm(request.form)
        if form.validate_on_submit():
            user = User(form.data)
            db.session.add(user)
            db.session.commit()
            session['username'] = user.username
            return redirect(url_for('views.profile', username=user.username))
        else:
            return render_template('sign_up.html', form=form)

        

@profiles_module.route('/profiles/<username>/comment/', methods=('POST',))
def submit_comment(username):
    if not g.user:
        flash("You are not authorized for that action.")
        return redirect(url_for('views.profiles'))
    form = CommentForm(request.form)
    user = User.get_user(username)
    if form.validate_on_submit():
        commenter = g.user
        comment = Comment(user.id, commenter.id, form.comment.data)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('views.profile', username=user.username))

    flash("There was an error with you comment.")
    return redirect(url_for('views.profile', username=user.username))



@profiles_module.route('/terms/')
def terms():
    return render_template('terms.html')

@profiles_module.route('/feedback/', methods=('GET','POST'))
def feedback():
    if request.method == 'GET':
        return render_template('feedback.html',
                form=FeedbackForm())

    form = FeedbackForm(request.form)
    if form.validate_on_submit():
        feedback = Feedback(form.name.data,
                            form.email.data,
                            form.message.data)
        db.session.add(feedback)
        db.session.commit()
        flash('Thank you for your comment!')
        return redirect(url_for('views.profiles'))

    return render_template('feedback.html',
            form=form)


@profiles_module.route('/add_buddy/<username>/')
def add_buddy(username):
    if not g.user:
        flash('You must be logged in to add buddies.')
        return redirect(url_for('views.profile',username=username))

    buddy_user = User.get_user(username)
    if g.user.id == buddy_user.id:
        flash('You may not add yourself as a buddy.')
        return redirect(url_for('views.profile',username=username))

    buddy = Buddy(g.user.id, buddy_user.id) 
    db.session.merge(buddy)
    db.session.commit()
    return redirect(url_for('views.profile',username=username))

@profiles_module.route('/profiles/<username>/private_message/', methods=('GET','POST'))
def private_message(username):
    if not g.user:
        flash('You are not authorized for that action.')
        return redirect(url_for('views.profile', username=username))

    profile_user = User.get_user(username)
    if request.method == 'GET':
        return render_template('private_message.html',
                form=PrivateMessageForm(),
                profile_user=profile_user)
    else:
        form = PrivateMessageForm(request.form)
        if form.validate_on_submit():
            pm = PrivateMessage(profile_user.id, 
                                g.user.id, 
                                form.subject.data, 
                                form.message.data)
            db.session.add(pm)
            db.session.commit()
            return redirect(url_for('views.profiles', username=username))
        else:
            return render_template('private_message.html',
                form=form,
                profile_user=profile_user)



@profiles_module.route('/private_messages/')
def private_messages():
    if not g.user:
        flash('You are not authorized for that action')
        return redirect('/')

    return render_template('private_messages.html')

@profiles_module.route('/delete_pm/<int:pm_id>/')
def delete_pm(pm_id):
    pm = PrivateMessage.query.get_or_404(pm_id)
    if not (g.user and g.user.id == pm.receiver_id):
        flash('You are not authorized for that action.')
        return redirect('/')
    db.session.delete(pm)
    db.session.commit()
    return redirect(url_for('private_messages'))

@profiles_module.route('/clear_visitors/')
def clear_visitors():
    if not g.user:
        flash('You are not authorized for that action.')
        return redirect('/')

    for v in Visit.query.filter(User.id == g.user.id):
        db.session.delete(v)

    db.session.commit()
    flash('Visitors have been cleared.')
    return redirect(url_for('views.profile', username=g.user.username))

