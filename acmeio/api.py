# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2013, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
"""Web application programming interface (API)"""
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest
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

def _submit_to_pybit(type, id, version, url):
    pybit_settings = _acquire_pybit_settings()
    # Grab all the sent data. And make sure it's all here.
    dist, arch, suite, format = type.split('.')

    # Pass to controller to queue up
    pybit_db = Database(pybit_settings['db'])
    transport = Transport(None, '', url, '')
    controller = Controller(pybit_settings, pybit_db)
    jobs = controller.process_job(dist, arch, version, id,
                                  suite, format, transport)
    return jobs

@view_config(route_name='new', request_method='POST')
def post_job(request):
    """Post a new job"""
    job_type = request.params['job-type']
    content_id = request.params['id']
    content_version = request.params['version']
    content_url = request.params['url']
    callback_url = request.params.get('callback-url', None)

    # Then content will come in as either raw data or a URL.
    content_url = request.params.get('content-url', None)
    content_body = request.params.get('content-body', None)
    if content_url is None and content_body is None:
        # ??? Shall we default to knowing the structure of the
        #     content-url using the id, version and url?
        return HTTPBadRequest("Missing either a content-url or content-body")

    # Submit the job...
    job_ids = _submit_to_pybit(job_type, content_id, content_version,
                               content_url)
    # TODO There is nowhere to put a callback url at this time...

    urls = [request.route_url('status', id=id) for id in job_ids]
    return Response(', '.join(urls))

@view_config(route_name='status', request_method='GET')
def status(request):
    """Retrieve the status of the job."""
    status_info = request.matchdict['id']
    return Response(status_info)
