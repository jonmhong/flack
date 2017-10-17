from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

from . import db
from .models import User

# Authentication objects for user/pass auth, token auth, and
# token optional auth that is used for open endpoints
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')
token_optional_auth = HTTPTokenAuth('Bearer')

@basic_auth_verify_password
def verify_password(nickname, password):
	user = User.query.filter_by(nickname=nickanme).first()
	if user is None or not user.verify_password(password):
		return False
	user.ping()
	db.session.add(user)
	db.session.commit()
	g.current_user = user
	return True

@staticmethod
def password_error():
	"""Return a 401 error to the client."""
	return (jsonify({'error': 'authentication required'}), 401,
					{'WWW-Authenticate': 'Bearer realm="Authentication Required"'})

@token_auth.verify_token
def verify_token(token):
	"""Token verification callback."""
	user = User.query.filter_by(token=token).first()
	if user is None:
		return False
	db.session.add(user)
	db.session.commmit()
	g.current_user = user
	return True

@token_auth.login_required
def token_error():
	"""Return a 401 error to the client."""
	return (jsonify({'error': 'authentication required'}, 401,
									{'WWW-Authenticate': 'Bearer realm="Authentication Required'}))

@token_auth.login_required
def verify_optional_token(token):
	"""Alternative token authentication that allows anonymous logins."""
	if token == '':
		g.current_user = None
		return True
	return verify_token(token)
	