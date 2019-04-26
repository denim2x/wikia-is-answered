from urllib.error import HTTPError

from pyquery import PyQuery as pq

from util import *

class Selector(tuple):
  def __new__(cls, *data):
    return tuple.__new__(cls, data)

  def __str__(self):
    return self._str

  def replace(self, *args):
    return str(self).replace(*args)

class Inclusion(Selector):
  def __init__(self, *data):
    self._str = ', '.join(f'#{e}' for e in data)

class Exclusion(Selector):
  def __init__(self, *data):
    self._str = ''.join(f':not(#{e})' for e in data)

_excludes = Exclusion(
  'Recommended_Readings',
  'See_Also',
  'Residents',
)

scrape_excludes = Exclusion(
  *_excludes,
  'Links_and_References',
  'References',
  'Points_of_Interest',
  'Links'  
)

with_h3 = Inclusion(
  'Paraphernalia', 
  'Alternate_Reality_Versions'
)

@attach(pq.fn)
def content():
  if not hasattr(this, '_content'):
    this._content = this.find('.mw-content-text')
    this._content.find('.noprint, noscript, script, style, link, iframe, embed, video, img, .editsection').remove()
    this._content.find('*').remove_attr('style')
  return this._content

def parse(**kw):
  key, val = next(iter(kw.items()))
  kw = { key: make_url(val) if key is 'url' else val }
  try:
    doc = pq(**kw)
    doc.title, doc.site = (e.strip() for e in doc.children('head > title').text().split('|', 2))[:2]
    return doc
  except HTTPError:
    pass

def _scrape(doc):
  content = doc.content()
  for ref in content.find('.reference').items():
    ref.attr('data-ref', ref.text().strip('[]'))
    ref.text('')
  for quote in content.find('.quote').items():
    author = quote.find('.selflink').closest('b')
    author.closest('dl').remove()
    text = quote.find('i')
    text.text('"' + text.text().strip('"\'').strip() + '"')
    author.append('said').prependTo(text.closest('dd'));
  sections = []
  headlines = content.children(f'h2{scrape_excludes} > {scrape_excludes}').closest('h2')
  for h in headlines.items():
    sel = 'p, ul, ol, .quote'
    sel = f'h3, {sel}' if h.children(with_h3) else sel
    h.body = h.nextUntil('h2', sel)
    sections.append(h)
  doc.sections = sections
  return doc

def scrape(doc):
  _scrape(doc)
  res = []
  for section in doc.sections:
    res.extend(e.text().strip() for e in section.body.items())
  return '\n'.join(s for s in res if s)
