import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# bootstrap: a blueprint [allows for scaling large applications]
from flask_bootstrap import Bootstrap
from config import config

# initialize extensions
db = SQLAlchemy()
bootstrap = Bootstrap()

from .models import models

# this is the factory
def create_app(config_name=None):
	# configure it
	if config_name is None:
		config_name = os.environ.get('FLACK_CONFIG', 'development')
	app = Flask(__name__)
	app.config.from_object(config[config_name])

	# initialize app
	db.init_app(app)
	bootstrap.init_app(app)

	from .flack import main as main_blueprint
	app.register_blueprint(main_blueprint)

	from .api import api as api_blueprint
	app.register_blueprint(api_blueprint, url_prefix='/api')

	return app


def run():
	os.environ['DATABASE_URL'] = 'sqlite://'
	os.environ['FLACK_CONFIG'] = 'testing'

	cov = coverage.Coverage(branch=True)
	