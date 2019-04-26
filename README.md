# WikiA is Answered

An engaging virtual assistant service for answering (almost) any question about some event or character from the Fandom/WikiA knowledge base

## Architecture
- designed for the [Google Cloud Platform](https://cloud.google.com/)
- *Python* server ([*bareASGI*](https://bareasgi.readthedocs.io/en/latest/)), running on [*App Engine Flexible Environment*](https://cloud.google.com/appengine/docs/flexible/)
- *conversational agent* running on [*Dialogflow*](https://dialogflow.com/)
- *Redis* database running on [*Cloud Memorystore*](https://cloud.google.com/memorystore/)
- [*Custom Search* engine](https://www.google.com/cse/) for retrieving articles from [*Fandom*](https://www.fandom.com/)

### Dialogflow agent
- *welcome* and *fallback* intents (as per *default*)
- *identity* intent (e.g. *'To whom am I speaking?'*')
- *description* intent (e.g. *'Please describe yourself'*)
- *workflow* intent (e.g. *'What may I ask about?'*)
- dynamic *knowledge base* (new documents added as necessary)

## Workflow
- the user is greeted with an introductory *message* from the *Dialogflow* agent
- the user may submit a message (usually a question) using the input area
- the server sends the question to the *Dialogflow* agent, thus obtaining a list of potential *answers* (excluding the *knowledge base*)
- if no relevant answers are found, the query is sent to the *Custom Search* engine and a list of articles is thus obtained
- each article is checked for existence in the *Redis* database (by URL) and, if necessary, *scraped* and then stored (in *plain text*) in the *agent's* *knowledge base*
- the input query is then sent once more to the agent and the *knowledge base* answers are retrieved and filtered such that all resulting answers's source URLs are also present in the search results
- if the list of answers is non-empty, the most relevant answer is displayed on the *frontend* - otherwise the *fallback* message is displayed
- this process can be repeated indefinitely

## Setup
### Requirements
- *<project root>/account.json* with valid *GCP service account* data
- *<project root>/config.yaml* with the following:
```yaml
google_api:
  key: <API key>

custom_search:
  cx: <Custom Search ID>
  
redis:
  - host: <host>
    port: <port>
  - ...
```

The Redis credentials are tried sequentially until a successful database connection is established.

## MIT Lincense
