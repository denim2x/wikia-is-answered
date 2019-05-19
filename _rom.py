from rom import *
import rom as _rom
from rom.columns import String as _String
from rom.util import set_connection_settings as init, get_connection


class String(_String):
  def _to_redis(self, value):
    if isinstance(value, bytes):
      return super()._to_redis(value)
    return value

class _Model:
  def __getitem__(self, key):
    value = getattr(self, key)
    return value.decode() if isinstance(value, bytes) else bytes

Model = (_Model, _rom.Model)

def bgsave():
  db = get_connection()
  try:
    db.bgsave()
    return True
  except:
    return False
