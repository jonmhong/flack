#!/usr/bin/env python

# manage.py supports the application factory pattern
from flask_script import Manager
from flack import create_app, db

manager = Manager(create_app)


@manager.command
def create_db(drop_first=False):
	"""Creates the database."""
	if drop_first:
		db.drop_all()
	db.create_all()


if __name__ == '__main__':
	manager.run()
