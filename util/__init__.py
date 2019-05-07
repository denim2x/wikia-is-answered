import os
from platform import python_version_tuple as get_pyversion

from pyquery import PyQuery as pq

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
