#!/usr/bin/env python2
from flask import Flask, render_template
from profiles.models import db, User

from profiles.views import profiles_module
from profiles.forms import LoginForm
from flaskext.uploads import configure_uploads, patch_request_class
import settings
import pretty
from babel.dates import format_datetime, format_date
from jinja2 import Markup

def configure_app(app):
    # load configs
    app.config.from_object(settings)

    # set up photo upload set    
    configure_uploads(app, [settings.PHOTO_UPLOAD_SET])
    patch_request_class(app, 2 * 1024 * 1024)

    # apply app to extentions
    db.init_app(app)
    with app.test_request_context():
        db.create_all()

    # register modules
    app.register_module(profiles_module)


    # setup error pages
    @app.errorhandler(404)
    @app.errorhandler(500)
    def page_not_found(error):
        return render_template('page_not_found.html'), 404

    # setup jinja filters
    app.jinja_env.filters['pretty_date'] = pretty.date
    app.jinja_env.filters['format_datetime'] = lambda d: format_datetime(d, locale=settings.LOCALE)
    app.jinja_env.filters['format_date'] = lambda d: format_date(d, locale=settings.LOCALE)

    # setup logger
    if not app.debug:
        from logging import FileHandler, WARNING, Formatter

        file_handler = FileHandler(settings.LOG_FILE)
        file_handler.setLevel(WARNING)
        file_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)

app = Flask(__name__)
configure_app(app)

if __name__ == '__main__':
    app.run()
