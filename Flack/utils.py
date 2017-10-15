import time

# _request_ctx_stack: 
from flask import url_for as _url_for, current_app, _request_ctx_stack
def timestamp():
	"""Return the current timestamp as an integer."""
	return int(time.time())

def url_for(*args, **kwargs):
	"""
	url_for replacement that works even when there is no request context.
	"""
	if '_external' not in kwargs:
		kwargs['_external'] = False
	# global stack is created to be available for all threads
	reqctx = _request_ctx_stack.top
	if reqctx is None:
		if kwargs['_external']:
			raise RuntimeError("Cannot generate external URLs without a request context.")

			with current_app.test_request.context():
				return _url_for(*args, **kwargs)