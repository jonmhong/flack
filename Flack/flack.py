import os
import threading
import time
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
# screen scraper
from bs4 import BeautifulSoup
from . import stats
from .api import api as api_blueprint
from config import config
from .stats import request_stats
from .utils import timestamp, url_for

# set base directory
basedir = os.path.abspath(os.path.dirname(__file__) + '/..')

app = Flask(__name__)
# os.environ.get: access environment variables in 
app.config.from_object(config[os.environ.get('FLACK_CONFIG', 'development')])
# in place of routes when breaking down app
app.register_blueprint(api_blueprint, url_prefix='/api')

# initialize extensions
db = SQLAlchemy(app)
Bootstrap(app)

from .models import User, Message


@app.before_first_request
def before_first_request():
	"""Start a background thread that looks for users that leave."""
	def find_offline_users():
		while True:
			User.find_offline_users()
			db.session.remove()
			time.sleep(5)

	if not app.config['TESTING']:
		thread = threading.Thread(target=find_offline_users)
		thread.start()

@app.before_request
def before_request():
	"""Update requests per second stats."""
	stats.add_request()

# Routes

@app.route('/')
def index():
	"""Serve client side application"""
	return render_template('index.html')

@app.route('/stats', methods=['GET'])
def get_stats():
	return jsonify({'requests_per_second': stats.requests_per_second()})