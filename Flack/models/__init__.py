from flask import Blueprint

model = Blueprint('models', __name__)

from . import User, Messages