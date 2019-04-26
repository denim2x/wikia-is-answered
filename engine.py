import os, json, re
from math import inf

from walrus import Database
from bareasgi import text_reader

from util import *
from scraper import scrape, parse
from search import Search
from dialogflow import Dialogflow

google_api = config['google_api']
search = Search(google_api['key'], config['custom_search']['cx'])

from uuid import uuid1
ping = bytes(str(uuid1()), 'utf-8')
for _redis in config['redis']:
  try:
    db = Database(host=_redis['host'], port=_redis['port'], password=_redis.get('pass'), db=0)
    if ping == db.execute_command('ECHO', ping):
      db_error = None
      break
  except Exception as e:
    db_error = e
    pass

if db_error:
  print('[WARN] Redis connection failed: ', db_error)
  db = None
else:
  url_db = db.Hash('urls')

dialogflow = Dialogflow()

kb_dict = {}
for kb in dialogflow.knowledge_bases():
  kb_dict[kb.display_name] = kb.name

async def knowledge(scope, info, matches, content):
  res = []
  for name, path in kb_dict.items():
    docs = []
    for doc in dialogflow.documents(path):
      docs.append({ 'caption': doc.display_name, 'url': url_db.get(doc.name, b'').decode() or None })
    res.append({ 'caption': name, 'documents': sorted(docs, key=lambda e: e['caption']) })
  return json_response(sorted(res, key=lambda e: e['caption']))

async def respond(scope, info, matches, content):
  text = re.sub(r'\s+', ' ', (await text_reader(content)).strip().lstrip('.').strip())
  if text == '':
    return json_response([dialogflow.event('WELCOME')])

  answers = dialogflow.get_answers(text, kb=False)
  if answers:
    return json_response(answers)

  query = text.strip('?!').strip()
  if not query:
    return 400

  docs = str_set()
  for e in search(query)[:10]:
    if e['url'] in db:
      path = db[e['url']]
      docs.add(path)
      url_db[path] = e['url']
    else:
      print('[INFO] Generating document:', e['url'])
      doc = parse(url=e['url'])
      if doc is None:
        print('[WARN] URL request failed:', e['url'])
        continue
      if doc.site not in kb_dict:
        print('[WARN] Missing knowledge base:', doc.site)
        continue
        db[e['domain']] = dialogflow.init(doc.site).name
      res = dialogflow.store(kb_dict[doc.site], doc.title, scrape(doc))
      if res is None:
        print('[WARN] Document creation failed:', e['url'])
        continue
      print('[INFO] Document created:', res.name)
      db[e['url']] = res.name
      url_db[res.name] = e['url']
      docs.add(res.name)

  db.bgsave()

  answers = dialogflow.get_answers(text, filter=lambda a: a.source in docs)
  if answers:
    return json_response(answers)

  return json_response([dialogflow.event('fallback')])
