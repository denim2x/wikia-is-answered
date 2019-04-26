from uuid import uuid4

from dialogflow_v2beta1 import SessionsClient, KnowledgeBasesClient, DocumentsClient
from dialogflow_v2beta1 import types as dialogflow
from dialogflow_v2beta1 import enums
from google.api_core.exceptions import InvalidArgument, GoogleAPICallError

from util import *

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
  
class Dialogflow:
  def __init__(self, session_id=uuid4(), language_code='en'):
    self.session_id = session_id
    self._session = session.session_path(project_id, session_id)
    self._kb = kb.project_path(project_id)
    self.language_code = language_code
    self.min_confidence = 0.8

  def init(self, name):
    return kb.create_knowledge_base(self._kb, dialogflow.KnowledgeBase(display_name=name))

  def store(self, container, title, text):
    doc = dialogflow.Document(
      display_name=title, mime_type='text/plain', 
      knowledge_types=EXTRACTIVE_QA, content=text)
    try:
      return docs.create_document(container, doc).result()
    except (InvalidArgument, GoogleAPICallError):
      res = [d for d in self.documents(container) if d.display_name == title]
      return res[0] if res else None

  def __call__(self, text=None, event=None):
    language_code = self.language_code
    if text is not None:
      text_input = dialogflow.TextInput(text=text, language_code=language_code)
      query_input = dialogflow.QueryInput(text=text_input)
    elif event is not None:
      event_input = dialogflow.EventInput(name=event, language_code=language_code)
      query_input = dialogflow.QueryInput(event=event_input)
    else:
      return None
    return session.detect_intent(session=self._session, query_input=query_input)

  def get_answers(self, text, raw=False, kb=True, sort_key=None, **kw):
    res = self(text=text)
    filter_fn = kw.get('filter')
    if hasattr(res.query_result, 'knowledge_answers'):
      if not kb and res.alternative_query_results:
        answer = res.alternative_query_results[0]
        if answer.intent_detection_confidence >= self.min_confidence:
          return [answer.fulfillment_text]
        return None
      answers = [a for a in res.query_result.knowledge_answers.answers]
      if filter_fn:
        answers = list(filter(filter_fn, answers))
      if sort_key:
        answers.sort(sort_key)
      return answers if raw else [a.answer for a in answers]
    return None

  def event(self, name, raw=False):
    res = self(event=name)
    return res if raw else res.query_result.fulfillment_text

  def knowledge_bases(self):
    return kb.list_knowledge_bases(self._kb)

  def documents(self, container):
    name = container
    if not isinstance(container, str):
      name = container.name
    return docs.list_documents(name)
