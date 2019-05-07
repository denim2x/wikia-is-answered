from urllib.error import HTTPError
from collections import namedtuple

from util import pq, List


_excludes = (
  'Recommended_Readings',
  'See_Also',
  'Residents',
  'Paraphernalia',
  'Alternate_Reality_Versions'
)

scrape_excludes = List(
  [
    *_excludes,
    'Links_and_References',
    'References',
    'Points_of_Interest',
    'Links'
  ],
  format=':not(#{item})',
  str=''
)

Fragment = namedtuple('Fragment', ('caption', 'text'))

def _text(el, to_strip=None):
  if el is None:
    return None
  return el.text().strip().strip(to_strip).strip()
  
class Document:
  def __init__(self, url=None, name=None, quotes=False):
    if name is not None:
      url = url.format(*name.split('|'))
      self.name = name
    else:
      self.name = '|'.join([url.subdomain, url.basename])

    self.url = str(url)
    try:
      doc = pq(url=self.url)
    except HTTPError:
      doc = pq([])
    self.caption = doc.children('head > title').text().split('|', 1)[0].strip()
    self.site = doc.find('link[rel="search').attr('title').rstrip('(en)').strip()
    self._doc = doc
    self.__content = None
    self._data = None
    self._quotes = quotes
    sel = List(['h3, p, ul, ol'])
    if self._quotes:
      sel.append('.quote')
    self._sel = str(sel)

  def __bool__(self):
    return bool(self._doc)

  def _content(self):
    if self.__content is None:
      content = self._doc.find('.mw-content-text')
      content.find('.noprint, noscript, script, style, link, iframe, embed, video, img, .editsection').remove()
      content.find('*').remove_attr('style')
      self.__content = content
    return self.__content

  def __iter__(self):
    if not self:
      return

    if self._data is not None:
      yield from self._data

    self._data = []
    content = self._content()
    content.find('.reference').remove()
    if self._quotes:
      for quote in content.find('.quote').items():
        author = quote.find('.selflink').closest('b')
        author.closest('dl').remove()
        _quote = quote.find('i')
        _quote.text('"' + _text(_quote, '"\'') + '"')
        author.append('said').prependTo(_quote.closest('dd'))
    
    h2_list = content.children(f'h2{scrape_excludes} > {scrape_excludes}').closest('h2')
    for h2 in h2_list.items():
      self._append(h2.nextUntil('h2, h3', self._sel), h2)
      for h3 in h2.nextUntil('h2', 'h3'):
        self._append(h3.nextUntil('h2, h3', self._sel), h2, h3)

  def _append(self, body, *heads):
    _data = self._data
    if _data is None or not body:
      return False

    caption = List((_text(h) for h in heads), str='/')
    text = List((_text(e) for e in body.items()), False, str='\n')
    _data.append(Fragment(f"{self.name}#{caption}", str(text)))
    return True

  @staticmethod
  def parse_name(name):
    name, heads = name.split('#')
    return name, heads.split('/')
