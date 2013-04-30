Transformation Service
======================

This application is an interface to submitting and monitoring jobs
sent to a message queue (e.g. RabbitMQ).

API
---

The API consists of two routing paths, one for posting and one for
checking the status of a job.

* `Job creation`_
* Job status

Job creation
------------

To create a new job, we post data to ``/`` with the following fields
and values.

job-type
  This is a string of dot separated values. The syntax of this value
  is as follows:
  ``<platform>.<architecture>.<suite(princexml|latex)>.<transform>``.
  For example, ``cnx..princexml.epub`` to build a CNX branded EPub
  using the princexml transforms engine.

Mutually exclusive fields:

content-url
  A URL to a piece of content accesible to the transformation code,
  which likely means public. 

content-body
  The raw content.

Optional fields used to enable repository content discovery:

url
  The base URL to a repository, archive or web view instance. (I
  imagine that these times of applications will at some point have
  type discovery on them so that we use the correct interfacing.)

id
  The ID of the content in the repository. 

version
  The version of the content that the transform should work
  against. This will default to ``latest``.

Optional field for job status updating:

callback-url
  A URL that is pinged after the tranformation has been completed. (The
  details of this callback have not yet been worked out. For example,
  is this a simple GET against the URL or are we posting info?)

On a successful post, the response will be a URL where the submitting
party can watch the status of the job.

202 - with supply status url

Job status
----------

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

Additional routes
-----------------

GET / - job-type info
GET /status - Listing of all jobs
