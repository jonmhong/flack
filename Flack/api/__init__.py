from Flask import Blueprint

api = Blueprint('api', __name__)

from . import tokens, users, messages