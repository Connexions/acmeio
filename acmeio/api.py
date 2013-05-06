# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2013, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
"""Web application programming interface (API)"""
from urlparse import urlparse
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import (
    HTTPOk, HTTPAccepted,
    HTTPBadRequest, HTTPInternalServerError,
    )
from pyramid.threadlocal import get_current_registry

from amqplib import client_0_8 as amqp
import jsonpickle
import pybit
from pybitweb.controller import Controller as BaseController
from pybitweb.db import Database
from pybit.models import Transport, BuildRequest


class Controller(BaseController):
    """Overrides of pybitweb.controller.Controller"""

    def process_job(self, dist, architectures, version, name,
                    suite, pkg_format, transport, build_environment=None):
        """Overridden to return the build request ID"""
        current_package = self.process_package(name, version)
        if not current_package.id:
            raise Exception("Huh?")
            ##return False

        current_suite = self.db.get_suite_byname(suite)[0]
        current_dist = self.db.get_dist_byname(dist)[0]
        current_format = self.db.get_format_byname(pkg_format)[0]

        # FIXME The use of 'any' is evil. Let's kill this behavior.
        build_env_suite_arch = self.process_build_environment_architectures(
                current_suite, architectures, build_environment)

        if len(build_env_suite_arch) == 0:
            raise Exception("Unable to submit job to PyBit")
        else:
            current_build_env = build_env_suite_arch[0].buildenv
            master_flag = True

        chan = self.get_amqp_channel()
        jobs = []
        for build_env_suite_arch in build_env_suite_arch:
            current_arch = build_env_suite_arch.suitearch.arch
            if current_build_env and current_build_env.name != build_env_suite_arch.get_buildenv_name() : #FIXME
                #first packageinstance for each build environment should have master flag set
                master_flag = True
            current_build_env = build_env_suite_arch.buildenv
            current_packageinstance = self.process_packageinstance(current_build_env, current_arch, current_package, current_dist, current_format, current_suite, master_flag)
            if current_packageinstance.id is None:
                raise Exception("Package instance not found...")

            new_job = self.db.put_job(current_packageinstance,None)
            if new_job is None:
                raise Exception("Job not created...")

            self.cancel_superceded_jobs(new_job)
            build_request_obj = BuildRequest(new_job,transport,
                    "%s:%s" % (self.settings['web']['hostname'],
                               self.settings['web']['port']))
            build_req = jsonpickle.encode(build_request_obj)
            self.db.log_buildRequest(build_request_obj)
            msg = amqp.Message(build_req)
            msg.properties["delivery_mode"] = 2
            routing_key = pybit.get_build_route_name(
                new_job.packageinstance.get_distribution_name(),
                new_job.packageinstance.get_arch_name(),
                new_job.packageinstance.get_suite_name(),
                new_job.packageinstance.get_format_name())
            build_queue = pybit.get_build_queue_name(
                new_job.packageinstance.get_distribution_name(),
                new_job.packageinstance.get_arch_name(),
                new_job.packageinstance.get_suite_name(),
                new_job.packageinstance.get_format_name())
            self.add_message_queue(build_queue, routing_key, chan)

            chan.basic_publish(msg, exchange=pybit.exchange_name,
                               routing_key=routing_key, mandatory=True)

            jobs.append(new_job.id)
        return jobs


def _acquire_pybit_settings():
    """Find and produce the PyBit settings as PyBit would normally
    know and use them.

    """
    pybit_config_path = get_current_registry().settings['pybit-config-path']
    settings = pybit.load_settings(pybit_config_path)[0]
    return settings

def _get_pybit_database():
    settings = _acquire_pybit_settings()
    return Database(settings['db'])

def _submit_to_pybit(type, id, version, url):
    pybit_settings = _acquire_pybit_settings()
    # Grab all the sent data. And make sure it's all here.
    dist, arch, suite, format = type.split('.')

    # Pass to controller to queue up
    pybit_db = _get_pybit_database()
    transport = Transport(None, '', url, '')
    controller = Controller(pybit_settings, pybit_db)
    jobs = controller.process_job(dist, arch, version, id,
                                  suite, format, transport)
    return jobs

def _get_job_history(job_id):
    pybit_db = _get_pybit_database()
    return pybit_db.get_job_statuses(job_id)

@view_config(route_name='new', request_method='POST')
def post_job(request):
    """Post a new job"""
    job_type = request.params['job-type']
    callback_url = request.params.get('callback-url', None)

    # Then content will come in as either raw data or a URL.
    content_url = request.params.get('content-url', None)
    content_body = request.params.get('content-body', None)
    if content_url is not None:
        # XXX This information can be removed after PyBit has
        #     been factored out.
        url_parts = urlparse(content_url)
        base_url = "{}://{}/".format(
            url_parts.scheme and url_parts.scheme or 'http',
            url_parts.netloc,
            )
        # This assumes a (plone based) repository a URL path structure of
        #   /content/<id>/<version>
        id, version = url_parts.path.rstrip('/').split('/')[-2:]
    elif content_body is not None:
        # TODO Check content_body is an EPUB formatted piece of content.
        raise NotImplementedError()
    else:
        return HTTPBadRequest("Missing either a content-url or content-body")

    # Submit the job...
    job_ids = _submit_to_pybit(job_type, id, version, base_url)
    # TODO There is nowhere to put a callback url at this time...

    urls = [request.route_url('status', id=id) for id in job_ids]
    return Response(', '.join(urls))

@view_config(route_name='status', request_method='GET', renderer='json')
def status(request):
    """Retrieve the status of the job."""
    job_id = request.matchdict['id']
    job_history = _get_job_history(job_id)

    # XXX Not ideal to be checking for a particular status string...
    latest = job_history[-1]
    if latest.status == 'Done':
        request.response_status = '200 Ok'
        return ''
    elif latest.status in ('Blocked', 'Failed',):
        raise HTTPInternalServerError()

    tasks_completed = 0
    tasks_total = 1
    messages = [{'type': m.status, 'timestamp': m.time, 'message': ''}
                for m in job_history]
    data = {'tasks-completed': tasks_completed, 'tasks-total': tasks_total,
            'messages': messages, 'last-modified': latest.time,
            }
    request.response_status = '202 Accepted'
    return data
