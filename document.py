from urllib.error import HTTPError
from collections import namedtuple

from util import pq, List, Text, OrderedSet


_excludes = (
  'Recommended_Readings',
  'See_Also',
  'Residents',
  'Alternate_Reality_Versions'
)

scrape_excludes = List(
  [
    *_excludes,
    'Links_and_References',
    'References',
    'Points_of_Interest',
    'Links',
    'Related'
  ],
  format=':not(#{item})',
  str=''
)

Handle = namedtuple('Handle', ('pointer', 'until'))
Fragment = namedtuple('Fragment', ('handle', 'text'))

def _text(el, to_strip=None):
  if el is None:
    return None
  text = el.text() if isinstance(el, pq) else el
  return text.strip().strip(to_strip).strip()
  
class Document:
  def __init__(self, url=None, name=None, quotes=False, prepare=False):
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
    self.site = doc.find('link[rel="search"]').default('title', '').rstrip('(en)').strip()
    self._doc = doc
    self.__content = None
    self.__h2 = None
    self._fragments = None
    self._refs = True
    self._quotes = quotes
    self._isel = 'text, a, b, i, em, strong, span'
    sel = List([self._isel, 'p, ul, ol'])
    if self._quotes:
      sel.append('.quote')
    self._sel = str(sel)
    if prepare:
      iter(self)

  def __bool__(self):
    return bool(self._doc)

  def _content(self):
    if self.__content is None:
      content = self._doc.find('.mw-content-text')
      content.find('.noprint, noscript, script, style, link, iframe, embed, video, img, .editsection').remove()
      self.__content = content
    return self.__content

  def __iter__(self):
    if not self:
      raise StopIteration

    if self._fragments is not None:
      yield from self._fragments

    self._fragments = {}
    content = self._content()

    self._fragment(content.children('.portable-infobox'), name='Summary', until='#toc')
    h2_list = content.children(f'h2{scrape_excludes} > {scrape_excludes}').closest('h2')
    for h2 in h2_list.items():
      self._fragment(h2)
      for h3 in h2.nextUntil('h2', 'h3').items():
        self._fragment(h2, h3)

    yield from tuple(self._fragments)

  def _fragment(self, *pointer, name=None, until=None):
    if not name:
      name = '/'.join(_text(h) for h in pointer)

    name = f"{self.name}#{_text(name)}"
    fragment = Fragment(Handle(pointer[-1], until), None)
    self._fragments[name] = fragment

  def __getitem__(self, name):
    if name not in self._fragments:
      return

    handle, text = self._fragments[name]
    if text is not None:
      return text

    content = self._content()

    if self._refs:
      content.find('.reference').remove()
      self._refs = False

    if self._quotes:
      for quote in content.find('.quote').items():
        author = quote.find('.selflink').closest('b')
        author.closest('dl').remove()
        _quote = quote.find('i')
        _quote.text('"' + _text(_quote, '"\'') + '"')
        author.append('said').prependTo(_quote.closest('dd'))

      self._quotes = None

    pointer, until = handle
    if not until:
      until = 'h2, h3'

    if pointer.children('span').is_('#Abilities, #Equipment, #Transportation, #Weapons'):
      body = pq([])
      for li in pointer.nextUntil('h2, h3', 'ul').children('li').items():
        nodes = pq([])
        for node in li.contents().items(exclude='ul, b > a'):
          nodes.extend(Text(_text(node).lstrip(': ').rstrip() + ' ') if node.prev().is_('b > a') else node)
        body.extend(pq('<p>').append(nodes))
    else:
      body = pointer.nextUntil(until, self._sel)

    return self._create(name, body)

  def _create(self, name, body):
    fragment = self._fragments.get(name)
    if not body:
      del self._fragments[name]
      return

    text = List(banned=False, str='\n')
    span = List(banned=False, str=' ')
    for node in body.items():
      if node.is_(self._isel):
        span.append(_text(node))
      else:
        text.extend([str(span), _text(node)])
        span.clear()
    text.append(str(span))
    text_ = str(text)
    if not text_:
      del self._fragments[name]
      return

    self._fragments[name] = Fragment(fragment.handle, text_)
    return text_

  @staticmethod
  def parse_name(name):
    name, heads = name.split('#')
    return name, heads.split('/')
