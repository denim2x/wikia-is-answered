from math import ceil, inf
import re

from googleapiclient.discovery import build

from util import URL
from config import custom_search, google_api

site_priority = dict((e, i) for i, e in enumerate([
  'marvel', 'ironman', 'xmen', 'dc', 'batman', 'arkham', 'dcau', 'heroes', 'arkhamcity', 'agentsofshield', 'marvelcinematicuniverse', 'marvel-movies'
]))

_service = build('customsearch', 'v1', developerKey=google_api['key'])
_cx = custom_search['cx']
_cse = _service.cse()

def search(query, limit=30):
  num_pages = ceil(limit / 10)
  res = []
  for page in range(num_pages):
    out = _cse.list(q=query, cx=_cx, num=10, start=1+page*10).execute()
    for e in out['items']:
      url = URL(e['formattedUrl'], 'query')
      m = re.match(r'^.+?\(Earth-(\d+)\)$', url.basename)
      if m and m[1] != '616':
        continue
      m = re.match(r'^(.+?)_\(.+?\)$', url.basename)
      if m and url.subdomain == 'batman':
        continue
      res.append(url)
  return sorted(res, key=lambda e: site_priority.get(e.subdomain, inf))
