import os, yaml, json

from util import realpath


with open(realpath('config.yaml')) as f:
  locals().update(yaml.load(f, Loader=yaml.SafeLoader))

project_id = os.getenv('GOOGLE_CLOUD_PROJECT', None)
if not project_id:
  with open(realpath('account.json')) as f:
    _account = json.load(f)
    project_id = _account['project_id']

__all__ = (
  'google_api', 'custom_search', 'dialogflow', 'redis', 'project_id'
)
