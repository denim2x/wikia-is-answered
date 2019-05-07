import bareasgi as _bareasgi
from bareasgi import *

def json_response(data, status=200, headers={}):
  headers = [] # FIXME
  return _bareasgi.json_response(status, headers, data)
