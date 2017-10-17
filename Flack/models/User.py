import binascii
import os

from flask import abort
from werkzeug.security import generate_password_hash, check_password_hash
# Prevent cyclical import of each other. Will change in later versions
from .. import db, models
# url_for: generates an endpoint to the given endpoint
from ..utils import timestamp, url_for

class User(db.Model):
	"""The User model."""
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.Integer, default=timestamp)
	updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
	last_seen_at = db.Column(db.Integer, default=timestamp)
	nickname = db.Column(db.String(32), nullable=False, )
	password_hash = db.Column(db.String(256), nullable=False)
	token = db.Column(db.String(64), nullable=True, unique=True)
	online = db.Column(db.Boolean, default=False)
	messages = db.relationship('Message', lazy='dynamic', backref='user')
	# backref: a simple way to also declare a new property on User class
	# lazy: defines when SQLAlchemy will load data from db

	@property 
	def password(self):
		raise AttributeError('password is not a readable attribute')

	# simple decorator that ensures pass are hashed and salted
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
		self.token = None
		# revoke token if a user changes passwords

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def generate_token(self):
		"""Creates a 64 character long randomly generated token"""
		# os.urandom: generate a string of size random bytes
		# binascii.hexlify: convert to hexadecimal
		# utf-8: convert to browser readable characters, such as chinese writing
		self.token = binascii.hexlify(os.urandom(32)).decode('utf-8')
		return self.token

	def ping(self):
		"""Marks the user as recently seen and online."""
		self.last_seen_at = timestamp()
		last_online = self.online

	@staticmethod # call a method without an instance of the class
	def create(data):
		"""Create a new user."""
		user = User()
		user.from_dict(data, partial_update=False)
		return user

	def from_dict(self, data, partial_update=True):
		"""Import data from dictionary"""
		for field in ['nickname', 'password']:
			try:
				setattr(self, field, data[field])
			except KeyError:
				if not partial_update:
					abort(400)

	def to_dict(self):
		"""Export user to a dictionary"""
		return {
			'id': self.id,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
			'nickname': self.nickname,
			'last_seen_at': self.last_seen_at,
			'online': self.online,
			'_links': {
				'self': url_for('api.get_user', id=self.id),
				'messages': url_for('api.get_messages', user_id=self.id),
				'tokens': url_for('api.new_token')
			}
		}

	@staticmethod
	def find_offline_users():
		"""Find users that haven't been active and mark them as offline"""
		users = Users.query.filter(User.last_seen_at < timestamp() - 60,
															 User.online == True).all()

		for user in users:
			user.online = False
			db.session.add(user)
		db.session.commit()

		return users