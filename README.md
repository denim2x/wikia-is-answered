# WikiA is Answered

An engaging virtual assistant service for answering (almost) any question about some event or character from the Fandom/WikiA knowledge base

## Architecture
- designed for the [Google Cloud Platform](https://cloud.google.com/)
- [Python *server*](https://bareasgi.readthedocs.io/en/latest/), running on [*App Engine Flexible Environment*](https://cloud.google.com/appengine/docs/flexible/)
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
- the server sends the question to the *Dialogflow* agent and obtains the initial list *answers* (excluding the *knowledge base*)
- if there are no relevant answers in the list, the query is searched in the database; if found, its associated answer is shown to the user
- otherwise the query is sent to the *Custom Search* engine; a list of articles URLs is thus obtained
- each article URL is checked for existence in the database and, if necessary, *scraped* and stored in *plain text* in the *agent's* *knowledge base*
- the input query is then sent once again to the agent and the *knowledge base* answers are retrieved
- if available, the most relevant answer is shown; otherwise the *fallback* message is displayed
- this process can be repeated indefinitely

## Setup
### Requirements
- *Dialogflow* agent restored from `knowledge-agent.zip` (see *releases*):
  - the *Fandom* knowledge base ('https://{0}.fandom.com/wiki/{1}') - *enabled*, identified by `Fandom KB ID` (the part after '.../editKnowledgeBase/');
- *\<project root>/config.yaml* with the following:
```yaml
google_api:
  key: <API key>   # for Custom Search

custom_search:
  cx: <Custom Search ID>

dialogflow:
  fandom: <Fandom KB ID>

redis:
  - host: <host>
    port: <port>      # optional (default: 6379)
    auth: <password>  # optional
  - ...
```
- (optional) *\<project root>/account.json* with valid *GCP service account* data.

The Redis credentials are tried sequentially until the first successful database connection.

## Notes

There's a significant delay during answer retrieval - caused by latencies that occur during scraping and uploading new documents into the *knowledge base*.
There's room for improvement in that area.

## MIT License
