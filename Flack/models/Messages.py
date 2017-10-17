import binascii
import os

from flask import abort, g
from werkzeug.security import generate_password_hash, check_password_hash
from markdown import markdown
import bleach
# screen scraper
from bs4 import BeautifulSoup
import requests
from .. import db
# url_for: generates an endpoint to the given endpoint
from ..utils import timestamp, url_for


class Message(db.Model):
	__tablename__ = 'message'
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.Integer, default=timestamp)
	updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
	source = db.Column(db.Text, nullable=False)
	html = db.Column(db.Text, nullable=False)
	user = db.Column(db.Integer, db.ForeignKey('users.id'))

	@staticmethod
	def create(data, user=None, expand_links=True):
		"""Create a new message. The user is obtained from the context unless
		provided explicitly"""
		msg = Message(user=user or g.current_user)
		msg.from_dict(data, partial_update=False)
		return msg

	def from_dict(self, data, partial_update=True):
		"""Export message data from a dictionary."""
		for field in ['source']:
			try:
				setattr(self, field, data[field])
			except KeyError:
				if not partial_update:
					abort(400)

	def to_dict(self):
		"""Export message to a dictionary."""
		return {
			'id': self.id,
			'created_at': self.created_at,
			'updated_at': self.updated_at,
			'last_seen_at': self.last_seen_at,
			'source': self.source,
			'html': self.html,
			'user': self.user.id,
			'_links': {
				'self': url_for('api.get_message', id=self.id),
				'user': url_for('api.get_user', id=self.user.id)
			}
		}

	def render_markdown(self, source):
		"""Render markdown source to HTML with a tag whitelist."""
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
		self.html = bleach.linkify(bleach.clean(
			markdown(source, output_format='html'),
			tags=allowed_tags, strip=True))

	def expand_links(self):
		"""Expands any links referenced in the message."""
		if '<blockquote>' in self.html:
			return False
		changed = False
		for link in BeautifulSoup(self.html, 'html5lib').select('a'):
			url = link.get('href', '')
			try:
				rv = requests.get(url)
			except requests.exceptions.ConnectionError:
				continue
			if rv.status_code == 200:
				soup = BeautifulSoup(rv.text, '')
				title_tags = soup.select('title')
				if len(title_tags) > 0:
					title = title_tags[0].string.strip()
				else:
					title = url
				description = 'No description found.'
				for meta in soup.select('meta'):
					if meta.get('name', '').lower() == 'description':
						description = meta.get('content', description).strip()
						break
				tpl = ('<blockquote><p><a href="{url}">{title}</a></p>',
							 '<p>{desc}</p></blockquote')
				self.html += tpl.format(url=url, title=title, desc=description)
				changed = True
		return changed

	@staticmethod
	def on_changed_source(target, value, oldvalue, initiator):
		"""SQLAlchemy event that automatically renders the message to HTML."""
		target.render_markdown(value)
		target.expand_links()

# this registers a listener function for the given target
db.event.listen(Message.source, 'set', Message.on_changed_source)