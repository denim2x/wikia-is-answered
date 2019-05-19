import os
from uuid import uuid4

from dialogflow_v2beta1 import SessionsClient, KnowledgeBasesClient, DocumentsClient
from dialogflow_v2beta1 import types, enums
from google.api_core.exceptions import InvalidArgument, GoogleAPICallError
from google.api_core.retry import Retry

from util import realpath
from config import project_id

EXTRACTIVE_QA = [enums.Document.KnowledgeType.EXTRACTIVE_QA]
_account = realpath('account.json')
if os.path.isfile(_account):
  session = SessionsClient.from_service_account_json(_account)
  kb = KnowledgeBasesClient.from_service_account_json(_account)
  docs = DocumentsClient.from_service_account_json(_account)
else:
  session = SessionsClient()
  kb = KnowledgeBasesClient()
  docs = DocumentsClient()

class KnowledgeBase:
  def __init__(self, id):
    if isinstance(id, types.KnowledgeBase):
      self._path = id.name
      self.caption = id.display_name
    else:
      self._path = kb.knowledge_base_path(project_id, str(id))
      self.caption = kb.get_knowledge_base(self._path).display_name

  def __iter__(self):
    yield from docs.list_documents(self._path)

  def create(self, caption, text=None):
    if text is None:
      caption, text = caption
    doc = types.Document(
      display_name=caption, mime_type='text/plain',
      knowledge_types=EXTRACTIVE_QA, content=text)
    try:
      return docs.create_document(self._path, doc).result()
    except (InvalidArgument, GoogleAPICallError):
      res = [d for d in self if d.display_name == caption]
      return res[0] if res else None
  
class Dialogflow:
  def __init__(self, session_id=uuid4(), language_code='en'):
    self.session_id = session_id
    self._session = session.session_path(project_id, session_id)
    self._kb = kb.project_path(project_id)
    self.language_code = language_code
    self.min_confidence = 0.8
    self._retry = {
      'retry': Retry(),
      'timeout': 10
    }

  def __call__(self, text=None, event=None):
    language_code = self.language_code
    if text is not None:
      text_input = types.TextInput(text=text, language_code=language_code)
      query_input = types.QueryInput(text=text_input)
    elif event is not None:
      event_input = types.EventInput(name=event, language_code=language_code)
      query_input = types.QueryInput(event=event_input)
    else:
      return None
    return session.detect_intent(session=self._session, query_input=query_input, **self._retry)

  def get_answers(self, text, kb=True):
    res = self(text=text)
    if not hasattr(res.query_result, 'knowledge_answers'):
      return

    if not kb and res.alternative_query_results:
      answer = res.alternative_query_results[0]
      if answer.action != 'input.unknown' and answer.intent_detection_confidence >= self.min_confidence:
        return [answer.fulfillment_text]
      return None

    return res.query_result.knowledge_answers.answers

  def event(self, name, raw=False):
    res = self(event=name)
    return res if raw else res.query_result.fulfillment_text

  def __iter__(self):
    for item in kb.list_knowledge_bases(self._kb):
      yield KnowledgeBase(item)
