import re
from collections import defaultdict

from _bareasgi import text_reader, text_response, json_response
#from redis import StrictRedis
#from redis.exceptions import ResponseError
import _rom as rom

from config import dialogflow as _dialogflow, redis
from document import Document
from search import search
from dialogflow import Dialogflow, KnowledgeBase


from uuid import uuid1
ping = bytes(str(uuid1()), 'utf-8')
#ping = str(uuid1())
for server in redis:
  host, port = server['host'], int(server.get('port', '6379'))
  try:
    rom.init(host=host, port=port, password=server.get('auth'), decode_responses=False)
    db = rom.get_connection()
    #db = StrictRedis(host=server['host'], port=server['port'], password=server.get('pass'), db=0, decode_responses=True)
    if db is None:
      raise Exception

    if ping == db.execute_command('ECHO', ping):
      server = db.connection_pool.connection_kwargs
      print('[INFO] Redis connection:', f"{server['host']}:{server['port']}")
      break
  except Exception as e:
    print("[WARN] Redis connection failed:", e if str(e) else f'{host}:{port}')

class _Fragment(*rom.Model):
  path = rom.String(required=True, unique=True)
  name = rom.String(required=True, unique=True)
  document = rom.ManyToOne('_Document', required=True, on_delete='no action')

class _Document(*rom.Model):
  name = rom.String(required=True, unique=True)
  url = rom.String(unique=True)
  caption = rom.String(required=True)
  site = rom.String(default='<unknown>')
  fragments = rom.OneToMany('_Fragment')

dialogflow = Dialogflow()
fandom = KnowledgeBase(_dialogflow['fandom'])
_url = fandom.caption

# TODO: Delete database entries not present in Fandom KB
docs = defaultdict(list)
for fragment in fandom:
  if not _Fragment.get_by(path=fragment.name):
    name, heads = Document.parse_name(fragment.display_name)
    docs[name].append(fragment)

for name, fragments in docs.items():
  _doc = _Document.get_by(name=name)
  if not _doc:
    doc = Document(_url, name)
    _doc = _Document(name=name, url=doc.url, caption=doc.caption, site=doc.site)
  for fragment in fragments:
    _fragment = _Fragment(path=fragment.name, name=fragment.display_name, document=_doc)
rom.session.flush()

sites = defaultdict(dict)
async def knowledge(scope, info, matches, content):
  for _doc in _Document.query.all():
    sites[_doc['site']].setdefault(_doc['url'], _doc['caption'])

  res = []
  for site, docs in sites.items():
    _docs = ({'caption': caption, 'url': url} for url, caption in docs.items())
    res.append({ 'caption': site, 'documents': sorted(_docs, key=lambda e: e['caption']) })

  return json_response(sorted(res, key=lambda e: e['caption']))


from util import PriorityQueue
from phrase_metric import similarity, validate

# FIXME
def _search(self, text, threshold=0.8):
  keys = (key.decode() for key in db.hkeys(self))
  keys = ((similarity(text, key), key) for key in keys)
  s, key = max(keys, key=lambda k: k[0], default=(0, None))
  if s > threshold:
    return key

_save = db.hset

def find_answer(query):
  ret = _search('_answers', query)
  return db.hget('_answers', ret).decode() if ret else None

def save_answer(query, answer):
  _save('_answers', query, answer)
  rom.bgsave()
  return answer

async def message(scope, info, matches, content):
  text = re.sub(r'\s+', ' ', (await text_reader(content)).strip().lstrip('.').strip())
  if text == '':
    return text_response(dialogflow.event('WELCOME'))

  answers = dialogflow.get_answers(text, kb=False)
  if answers:
    return text_response(answers[0])

  query = text.strip('?!').strip()
  if not validate(query):
    return text_response(dialogflow.event('fallback'))

  answer = find_answer(query)
  if answer:
    return text_response(answer)
    
  fragments = PriorityQueue(5, lambda f, r: 1 - r)
  for url in search(query)[:3]:
    doc = Document(url)
    if not doc:
      print('[WARN] URL request failed:', doc.url)
      continue

    for fragment_name in doc:
      if _Fragment.get_by(name=fragment_name):
        print('[INFO] Found fragment:', fragment_name)
        continue

      print('[INFO] Generating fragment:', fragment_name)
      fragment = doc[fragment_name]
      if not fragment:
        print('[INFO] Skipping empty fragment:', fragment_name)
        continue

      fragments.add((doc, fragment_name, fragment), similarity(fragment, query))

  for doc, name, fragment in fragments:
    print('[INFO] Uploading fragment:', name)
    res = fandom.create(name, fragment)
    if res is None:
      print('[WARN] Fragment upload failed:', name)
      continue

    _doc = _Document.get_by(name=doc.name)
    if not _doc:
      _doc = _Document(name=doc.name, url=doc.url, caption=doc.caption, site=doc.site)
    _fragment = _Fragment(path=res.name, name=name, document=_doc)
    print('[INFO] Fragment uploaded:', name)

  rom.session.flush()

  #lambda a: _Fragment.get_by(path=a.source).document['url'] in urls)

  answers = dialogflow.get_answers(query)
  if not answers:
    return text_response(dialogflow.event('fallback'))

  answer = max(answers, key=lambda a: a.match_confidence * similarity(a.answer, query))

  return text_response(save_answer(query, answer.answer))
