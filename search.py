from math import ceil, inf
import re

from googleapiclient.discovery import build

from util import *

site_priority = dict([e, i] for i, e in enumerate([
  'marvel', 'ironman', 'dc', 'batman', 'arkhamcity', 'agentsofshield', 'marvelcinematicuniverse', 'marvel-movies', 'dcau', 'gotham'
]))

class Search:
  def __init__(self, key, cx):
    self.service = build('customsearch', 'v1', developerKey=key)
    self.cx = cx
    self.cse = self.service.cse()

  def __call__(self, query, limit=30):
    num_pages = ceil(limit / 10)
    res = []
    for page in range(num_pages):
      out = self.cse.list(q=query, cx=self.cx, num=10, start=1+page*10).execute()
      for e in out['items']:
        url = make_url(e['formattedUrl'])
        basename = os.path.basename(urlsplit(url).path)
        m = re.match(r'^.+?\(Earth-(\d+)\)$', basename)
        if m and m[1] != '616':
          continue
        domain = e['displayLink']
        site = domain.rstrip('.fandom.com')
        m = re.match(r'^.+?\(.+?\)$', basename)
        if m and site == 'batman':
          continue
        res.append({
          'url': url,
          'domain': domain,
          'priority': site_priority.get(domain.rstrip('.fandom.com'), inf)
        })
    return sorted(res, key=lambda e: e['priority'])
