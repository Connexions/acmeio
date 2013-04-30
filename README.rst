Transformation Service
======================

This application is an interface to submitting and monitoring jobs
sent to a message queue (e.g. RabbitMQ).

Installation
------------

Dependencies:

- Postgresql
- RabbitMQ
- PyBit (to be removed)

To install the package, use the following command::

    $ python setup.py install

You may need to change the values in ``pybit.conf``. See PyBit's
documentation for details.

There is a temporary addition to PyBit's SQL schema that ties into the
job information. You'll need to install this using::

    $ psql pybit
    > \i sql_addtions.sql

And to run the application use the following::

    $ pserve production.ini

API
---

The API consists of a few routing paths, one for posting and one for
checking the status of a job.

* Job creation
* Job status
* Job type information
* Job listing

Job creation
~~~~~~~~~~~~

To create a new job, we post data to ``/`` with the following fields
and values.

:job-type:
  This is a string of dot separated values. The syntax of this value
  is as follows: ``<context>.<platform>.<engine(princexml|latex)>.<format>``.

Mutually exclusive fields:

:content-url:
  A URL to a piece of content accesible to the transformation code,
  which likely means public. 

:content-body:
  The raw content.

Optional fields used to enable repository content discovery:

:url:
  The base URL to a repository, archive or web view instance. (I
  imagine that these times of applications will at some point have
  type discovery on them so that we use the correct interfacing.)

:id:
  The ID of the content in the repository. 

:version:
  The version of the content that the transform should work
  against. This will default to ``latest``.

Optional field for job status updating:

:callback-url:
  A URL that is pinged after the tranformation has been completed. (The
  details of this callback have not yet been worked out. For example,
  is this a simple GET against the URL or are we posting info?)

On a successful post response will an HTTP 202 with a URL. The URL can
be used by the submitting party to watch the state of the job.

If a problem with the submission occures, an HTTP 400 will result. A
response body containing an error message may be supplied, but can not
be relied upon.

Job status
~~~~~~~~~~

To watch the status of a submitted job you will need the job id. The
path to the status is ``/status/<job-id>``.

This URL will respond with either an HTTP 200 (Success), 202
(Accepted, In progress) or 500 (Error, Failure).

An HTTP 200 means the job has completed and everything went superbly.

An HTTP 202 means the job has not yet commpleted. Accompanying the
response is a content body in the JSON format. This content body
contains the following values:

:tasks-completed: (integer) Number of tasks completed
:tasks-total: (integer) Total number of tasks to be completed
:messages: (array) Messages in chronilogical order
:last-modified: (datetime) Indicates when the last status update was recieved

If the job fails to build due to unforeseen circumstances or author
invoked exceptions, the response will be an HTTP 500 with custom
response information as well as logging and traceback information if
available.

Job type info
~~~~~~~~~~~~~

Job type information is represented by a '.' (dot) separated value
that closely reflects the message queue exchange naming syntax. For
example, ``cnx..princexml.epub`` would build a CNX branded EPub using
the PrinceXML XML transforms engine. Note the absense of the second
value, meaning 'any' value should suffice. 

The format of the job type string is as follows:
``<context>.<platform>.<engine(princexml|latex)>.<format>``.

:context: A project or suite that may or may not effect layout and
  branding of the generated content.
:platform: A architecture or platform specification. If used, it may
  effect the dimensions, coloration, interactablity, etc. For
  example, the 'screenreader' platform may be used to, say make all
  text and images gray scale.
:engine: An XML or data processing engine used to transform XML based
  content to other formats.
:format: The format the transformation should result in. 

The values used to represent these options are discoverable via a GET
on the application root. The response of this request is a JSON object
keyed by option with sub-objects containing the name and descriptions
of each value.

The data structure of a GET on '/' looks something like this::

    {'context': [{'id': 'cnx', 'name': 'Connexions',
                  'description': 'Connexions formatting and branding'},
                 {'id': 'openstax', 'name': 'OpenStax College',
                  'description': 'OpenStax College formatting'}
                  ],
     'platform': [...],
     ...
     }

List of jobs with latest status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A GET on '/status' will provide a list of active jobs with their
latest status. The response is a JSON list of jobs that resembles the
following structure::

    {'1': <job-status-object>, '2': <job-status-object>}

And the job-status-object is similar to that returned from the status
URL, except it only contains one message rather than the entire
message history.
    
This service is only available to authenticated service
members. Unauthenticated members will recieve an HTTP 404 Not Found.

API Authentication
------------------

Authentication is done using an API Key. The API Key can be aquired
via a connecting Connexions Authentication services
instance. Optionally, an API Key may be manually configured in the
application settings (no Connexions Authentication service instance
required).

The following illustrates an HTTP request using the API Key for
authentication and authorization.
::

    GET /status HTTP/1.1
    ...
    Authorization: Key <api-key-goes-here>
    ...

Anonymous access to the API can be disabled in the application's
configuration. By default, anonymous API calls are allowed, but
restrictions apply at the application layer. Additional restrictions
may be applied at the webserver layer (contact your system
administrator for information).

Example Usage
-------------

The following example shows a job submission for a Collection named
col10001 version 1.1 at http://cnx.org/content. This job is being
submitted for a build of the CompleteZip using the Latex engine and
built against Connexions specific context on the desktop platform.
::

    $ curl --form job-type=cnx.desktop.latex.completezip \
    > --form id=col10001 --form version=1.1 \
    > --form url=http://cnx.org/content \
    > --form content-url=http://cnx.org/content/col10001 \
    > http://localhost:6543/
    http://localhost:6543/status/7

After the job is submitted we can check it's status using the
resulting URL.
::

    $ curl http://localhost:6543/status/7
    {"tasks-completed": 0, "tasks-total": 1,
     "messages": [{"timestamp": "2013-04-30 11:48:53.904134", "message": "", "type": "Waiting"}], 
     "last-modified": "2013-04-30 11:48:53.904134"}
