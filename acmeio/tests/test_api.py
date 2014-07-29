# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2013, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
"""\
Tests for the acmeio api.
"""
import unittest

try:
    from unittest import mock
except ImportError:
    import mock
from pyramid.httpexceptions import (HTTPInternalServerError,
    HTTPBadRequest)
    
from .. import api

class PdfTests(unittest.TestCase):

    def setUp(self):
        self.mock_request = mock.Mock()
        self.mock_request.matchdict = {'id' : 5}
    
    def mock_done(self, job_id):
        self.assertEquals(job_id, 5)
        latest = mock.Mock()
        latest.status = 'Done'
        return [latest]
    
    def mock_accepted(self, job_id):
        self.assertEquals(job_id, 5)
        latest = mock.Mock()
        latest.status = 'Accepted'
        latest.time = 'right now!'
        return [latest]
        
    def mock_blocked(self, job_id):
        self.assertEquals(job_id, 5)
        latest = mock.Mock()
        latest.status = 'Blocked'
        return [latest]
        
    def mock_submit(self, job_type, id, version, base_url):
        return [5]
        
    def test_status_ok(self):                
        with mock.patch('acmeio.api._get_job_history', self.mock_done):
            response = api.status(self.mock_request)
        self.assertEquals(response, '')
        self.assertEquals(self.mock_request.response_status, '200 Ok')
        
    def test_status_accepted(self):
        with mock.patch('acmeio.api._get_job_history', self.mock_accepted):
            response = api.status(self.mock_request)
        self.assertEquals(response['tasks-completed'], 0)
        self.assertEquals(response['tasks-total'], 1)
        messages= response['messages'][0]
        self.assertEquals(messages['timestamp'], 'right now!')
        self.assertEquals(messages['type'], 'Accepted')
        self.assertEquals(response['last-modified'], 'right now!')
        self.assertEquals(self.mock_request.response_status, '202 Accepted')
        
    def test_status_blocked(self):
        with mock.patch('acmeio.api._get_job_history', self.mock_blocked):
            self.assertRaises(HTTPInternalServerError, api.status, self.mock_request)
        
    def test_post_job(self):
        params = {'job-type':'cnx.desktop.latex.completezip',
                    'id':'col10642', 'version':'1.2', 
                    'url':'http://cnx.org', 
                    'content-url':'http://cnx.org/content/col10642/1.2/'}
        self.mock_request.params = params
        self.mock_request.route_url.return_value = 'http://localhost:6543/status/5'
        with mock.patch('acmeio.api._submit_to_pybit', self.mock_submit):
            response = api.post_job(self.mock_request)
        urls = response._app_iter
        self.assertEquals(len(urls), 1)
        self.assertEquals(urls[0], 'http://localhost:6543/status/5')
        self.assertEquals(response._status, '200 OK')
        self.mock_request.route_url.assert_called_with('status', id=5)
    
    def test_post_job_bad_request(self):
        params = {'job-type':'cnx.desktop.latex.completezip',
                    'id':'col10642', 'version':'1.2', 
                    'url':'http://cnx.org'}
        self.mock_request.params = params
        bad_request = api.post_job(self.mock_request)
        self.assertTrue(isinstance(bad_request, HTTPBadRequest))
        self.assertEquals(bad_request.detail, "Missing either a content-url or content-body")
    