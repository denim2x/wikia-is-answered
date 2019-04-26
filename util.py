from urllib.parse import urlsplit, urlunsplit, urljoin

import yaml, os, json
from pyquery import PyQuery as pq
import bareasgi

class str_dict(dict):
  def __setitem__(self, key, value):
    if isinstance(key, bytes):
      key = key.decode()
    return super().__setitem__(key, value)

class str_set(set):
  def add(self, val):
    if isinstance(val, bytes):
      val = val.decode()
    return super().add(val) 

def json_response(data, status=200, headers={}):
  headers = [] # FIXME
  return bareasgi.json_response(status, headers, data)

from platform import python_version_tuple as get_pyversion
_pyversion = tuple(int(e) for e in get_pyversion())

if _pyversion >= (3, 6, 0):
  OrderedDict = dict
else:
  from collections import OrderedDict

__dir__ = os.path.dirname(os.path.realpath(__file__))
def realpath(path):
  return os.path.join(__dir__, path)

with open(realpath('config.yaml')) as f:
  config = yaml.load(f, Loader=yaml.SafeLoader)

with open(realpath('account.json')) as f:
  account = json.load(f)

project_id = account['project_id']

def make_url(url, base=None):
  if base:
    url = urljoin(base, url)
  return urlunsplit((*urlsplit(url)[:3], '', ''))

class OrderedSet:
  def __init__(self, src=None):
    super().__init__()
    self._data = OrderedDict()

    if src:
      self.update(src)

  def update(self, *sources):
    for src in sources:
      for item in src:
        self.add(item)
    return self

  def difference_update(self, src):
    for src in sources:
      for item in src:
        self.discard(item)
    return self

  def add(self, item):
    if item in self:
      return False
    self._data[item] = None
    return True

  def __contains__(self, item):
    return item in self._data

  def discard(self, item):
    if item in self:
      return False
    del self._data[item]
    return True

  def remove(self, item):
    if not self.discard(item):
      raise KeyError

  def __iter__(self):
    yield from self._data

  def clear(self):
    if not self:
      return False
    self._data.clear()
    return True

  def __bool__(self):
    return bool(self._data)

  def __repr__(self):
    return f"{{{', '.join(self)}}}"

  def __len__(self):
    return len(self._data)

  def __getitem__(self, index):
    res = list(self)
    if index == slice(None):
      return res
    return res[index]

def attach(target):
  def deco(func):
    setattr(target, func.__name__, func)
    return func
  return deco

@attach(pq.fn)
def nextUntil(sel, filter=None):
  res = OrderedSet()
  for node in this.items():
    while True:
      node = node.next()
      if node.is_(sel) or not node:
        break
      if node.is_(filter):
        res.add(node[0])

  return pq(res[:])
