import os
from platform import python_version_tuple as get_pyversion
from statistics import mean as _mean, StatisticsError

from pyquery import PyQuery as pq, text as _text

pyversion = tuple(int(e) for e in get_pyversion())
if pyversion >= (3, 6, 0):
  OrderedDict = dict
else:
  from collections import OrderedDict

__dir__ = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/..')

def realpath(path):
  return os.path.join(__dir__, path)

def new(cls, *args, **kw):
  if not isinstance(cls, type):
    cls = type(cls)
  return cls(*args, **kw)

from .set import Set, OrderedSet
from .list import Tuple, List
from .url import URL
from .priority_queue import PriorityQueue
from itertools import islice

def attach(target):
  def deco(func):
    setattr(target, func.__name__, func)
    return func
  return deco

def mixin(target):
  exclude = { '__module__', '__dict__', '__weakref__', '__doc__', '__new__' }
  def deco(cls):
    for name, attr in cls.__dict__.items():
      if name in exclude:
        continue
      setattr(target, name, attr)
    return cls
  return deco
  
def mean(data, default=None):
  try:
    return _mean(data)
  except StatisticsError:
    return default

def casefold(self):
  return str(self).casefold()

class Text:
  _tag = 'text'
  _html = f'<{_tag}>'
  def __new__(cls, text, prev=None):
    return pq(cls._html).append(text or '').before(prev)

_text.INLINE_TAGS.update([Text._tag])

def _Text(node, prev=None):
  return Text(node, prev)[0] if isinstance(node, str) else node

_before = pq.before
@attach(pq.fn)
def before(other):
  if other is None:
    return this
  return _before(this, other)

#@attach(pq.fn)
def _iter(this):
  if not this:
    raise StopIteration
  prev = _Text(this[0])
  yield pq(prev)
  for node in islice(this, 1, None):
    if isinstance(node, str):
      elem = Text(node)
      yield elem.set(_prev=pq(prev))
      prev = elem[0]
    else:
      yield pq(node)
      prev = node

@attach(pq.fn)
def test(include=None, exclude=None):
  if not this.is_(include):
    return False

  if exclude and this.is_(exclude):
    return False

  return True

@attach(pq.fn)
def set(**kw):
  for name, val in kw.items():
    setattr(this, name, val)
  return this

_prev = pq.prev
@attach(pq.fn)
def prev(sel=None):
  if hasattr(this, '_prev'):
    return this._prev.filter(sel)
  return _prev(this, sel)
  
@attach(pq.fn)
def default(name, default=None):
  value = this.attr(name)
  return default if value is None else value

_items = pq.items
@attach(pq.fn)
def items(include=None, exclude=None):
  for node in _iter(this):
    if node.test(include, exclude):
      yield node

@attach(pq.fn)
def tail(sel=None):
  return pq([Text(e.tail)[0] for e in this]).filter(sel)

@attach(pq.fn)
def nextUntil(sel=None, filter=None):
  res = OrderedSet()
  if sel is None:
    sel = ':not(*)'
  for node in this.items():
    while True:
      res.update(node.tail(filter))
      node = node.next()
      if node.is_(sel) or not node:
        break
      if node.is_(filter):
        res.update(node)

  return pq(res[:])
