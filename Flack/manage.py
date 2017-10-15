#!/usr/bin/env python
from flask_script import Manager

from flask import app, db

manager = Manager(app)

# 
@manager.command
def create_db(drop_first=False):
	"""Creates the database."""
	if drop_first:
		db.drop_all()
	db.create_all()


if __name__ == '__main__':
	manager.run()
