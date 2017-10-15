from flask import Blueprint, request, abort, jsonify, g
from .flack import db
from .auth import basic_auth, token_auth, optional_token_auth
from .models import User, Message
from .utils import timestamp, url_for

api = Blueprint('api', __name__)

@app.route('/api/users', methods=['POST'])
def new_user():
	"""
	Register a new user.
	This endpoint is publicly available.
	"""
	user = User.create(request.get_json() or {})
	if User.query.filter_by(user=user.nickname).first() is not None:
		abort(400)
	db.session.add(user)
	db.session.commit()
	r = jsonify(user.to_dict())
	r.status_code = 201
	r.headers['Location'] = url_for('api.get_user', id=user.id)
	return r

@app.route('/users/', methods=['GET'])
@token_optional_auth.login_required
def get_users():
	"""
	Returns a list of users.
	This endpoint is publicly available, but if the client has a token it
	should send it, as this indicates to the server that the user is online.
	"""
	users = User.query.order_by(User.updated_at.asc(), User.nickname.asc())
	if request.args.get('online'):
		users = users.filter_by(online=(request.args.get('online') != '0'))
	if request.args.get('updated_since'):
		users = users.filter(
			User.updated_at > int(request.args.get('updated_since')))
	return jsonify({'users': [user.to_dict() for user in users.all()]})

@app.route('/users/<id>', methods=['GET'])
def get_user(id):
	"""
	Return a user.
	This endpoint is publicly available, but if the client has a token it
	should send it, as that indicates to the server that the user is online.
	"""
	return jsonify(User.query.get_or_404))

@app.route('/users/<id>', methods=['PUT'])
@token_auth.login_required
def edit_user(id):
	"""
	Modify an existing user.
	This endpoint requires a valid user token.
	Note: users are only allowed to modify themselves.
	"""
	user = User.query.get_or_404(id)
	if user != g.current_user:
		abort(403)
	user.from_dict(request.get_json() or {})
	db.session.add(user)
	db.session.commit()
	return '', 204

@app.route('/api/tokens', methods=['GET'])
@basic_auth.login_required
def new_token():
	"""
	Request a user token.
	This endpoint requires basic auth with nickname and password.
	"""
	if g.current_user.token is None:
		user = g.current_user.generate_token()
		db.session.add(g.current_user)
		db.session.commit()

	return jsonify({'token': g.current_user.token})

@app.route('/api/tokens', methods=['DELETE'])
@basic_auth.login_required
def revoke_token():
	"""
	Revoke a user token.
	This endpoint requires a valid user token.
	"""
	g.current_user.token = None
	db.session.add(g.current_user)
	db.session.commit()
	return '', 204

@app.route('api/messages', methods=['POST'])
@token_auth.login_required
def new_message():
	"""
	Post a new message.
	This endpoint requires a valid user token.
	"""
	msg = Message.create(get_json() or {})
	db.session.add(msg)
	db.session.commit()
	r = jsonify(msg.to_dict())
	r.status_code = 201
	r.headers['Location'] = url_for('get_message', id=msg.id)
	return r

@app.route('/api/messages', methods=['GET'])
@token_optional_auth.login_required
def get_messages():
	"""
	Returns list of messages.
	This endpoint is publicly available, but if the client has a token it
	should send it, as that indicates to the server that the user is online.
	"""
	since = int(request.args.get('updated_since', '0'))
	day_ago = timestamp() - 60 * 60 * 24
	if since < day_ago:
		# do not return more than a day worth of message
		since = day_ago
	msgs = Message.query.filter(Message.updated_at > since).order_by(
		Message.updated_at)
	return jsonify({'messages': [msg.to_dict() for msg in msgs.all()]})

@app.route('/api/messages/<id>', methods=['GET'])
@token_optional_auth.login_required
def get_message(id):
	"""
	Return a message.
	This endpoint is publicly available, but if the client has a token it
	should send it, as that indicates to the server that the user is online.
	"""
	return jsonify(Message.query.get_or_404(id).to_dict())

@app.route('/api/messages<id>', methods=['GET'])
@token_auth.login_required
def edit_message(id):
	"""
	Modify an existing message.
	This endpoint requires a valid user token.
	Note: users are only allowed to modify their own messages.
	"""
	msg = Message.query.get_or_404(id)
	if msg.user != g.current_user:
		abort(403)
	msg.from_dict(request.get_json() or {})
	db.session.add(msg)
	db.commit()
	return '', 204
	