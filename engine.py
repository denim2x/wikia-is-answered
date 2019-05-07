import re

from _bareasgi import text_reader, json_response
#from redis import StrictRedis
#from redis.exceptions import ResponseError
import rom
from rom import util as _rom, session

from config import dialogflow as _dialogflow, redis
from document import Document
from search import search
from dialogflow import Dialogflow, KnowledgeBase


from uuid import uuid1
ping = bytes(str(uuid1()), 'utf-8')
db_error = '<config>'
for server in redis:
  try:
    _rom.set_connection_settings(host=server['host'], port=server['port'], password=server.get('pass'), decode_responses=True)
    db = _rom.get_connection()
    #db = StrictRedis(host=server['host'], port=server['port'], password=server.get('pass'), db=0, decode_responses=True)
    if db is None:
      db_error = '<undefined>'
      continue
    if ping == db.execute_command('ECHO', ping):
      db_error = None
      break
  except Exception as e:
    db_error = e
    pass

if db_error:
  print('[WARN] Redis connection failed:', db_error)
  db = None
else:
  print('[INFO] Redis connection:', db.connection_pool.connection_kwargs['host'])

class _Fragment(rom.Model):
  path = rom.String(required=True, unique=True)
  name = rom.String(required=True, unique=True)
  document = rom.ManyToOne('_Document', required=True, on_delete='no action')

class _Document(rom.Model):
  name = rom.String(required=True, unique=True)
  url = rom.String(unique=True)
  caption = rom.String(required=True)
  site = rom.String(default='<unknown>')
  fragments = rom.OneToMany('_Fragment')

dialogflow = Dialogflow()
fandom = KnowledgeBase(_dialogflow['fandom'])
_url = fandom.caption

# TODO: Delete database entries not present in Fandom KB
docs = {}
for fragment in fandom:
  if not _Fragment.get_by(path=fragment.name):
    name, heads = Document.parse_name(fragment.display_name)
    docs.setdefault(name, set()).add(fragment)

for name, fragments in docs.items():
  _doc = _Document.get_by(name=name)
  if not _doc:
    doc = Document(_url, name)
    _doc = _Document(name=name, url=doc.url, caption=doc.caption, site=doc.site)
  for fragment in fragments:
    _fragment = _Fragment(path=fragment.name, name=fragment.display_name, document=_doc)
session.flush()

sites = {}
async def knowledge(scope, info, matches, content):
  for _doc in _Document.query.all():
    sites.setdefault(_doc.site, {}).setdefault(_doc.url, _doc.caption)

  res = []
  for site, docs in sites.items():
    _docs = ({'caption': caption, 'url': url} for url, caption in docs.items())
    res.append({ 'caption': site, 'documents': sorted(_docs, key=lambda e: e['caption']) })

  return json_response(sorted(res, key=lambda e: e['caption']))

async def message(scope, info, matches, content):
  text = re.sub(r'\s+', ' ', (await text_reader(content)).strip().lstrip('.').strip())
  if text == '':
    return json_response([dialogflow.event('WELCOME')])

  answers = dialogflow.get_answers(text, kb=False)
  if answers:
    return json_response(answers)

  query = text.strip('?!').strip()
  if not query:
    return 400

  urls = set()
  for url in search(query)[:10]:
    if not _Document.get_by(url=str(url)):
      doc = Document(url)
      print('[INFO] Generating document:', doc.name)
      if not doc:
        print('[WARN] URL request failed:', doc.url)
        continue
      _doc = _Document(name=doc.name, url=doc.url, caption=doc.caption, site=doc.site)
      for fragment in doc:
        res = fandom.create(fragment)
        if res is None:
          print('[WARN] Fragment creation failed:', fragment.caption)
          continue
        _fragment = _Fragment(path=res.name, name=fragment.caption, document=_doc)
      print('[INFO] Document created:', doc.name)

    urls.add(str(url))

  session.flush()

  answers = dialogflow.get_answers(text, filter=lambda a: _Fragment.get_by(path=a.source).document.url in urls)
  if answers:
    return json_response(answers)

  return json_response([dialogflow.event('fallback')])
