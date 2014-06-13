# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2013, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###

import json
import jsonpickle
import pika
import pyramid.paster
import re
import unittest
from webtest import TestApp
      
class AcmeioFunctionalTests(unittest.TestCase):
    
    channel = None
    
    def setUp(self):       
        # import and create a TestApp to test requests
        app = pyramid.paster.get_app('production.ini')
        self.testapp = TestApp(app)
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters('localhost', 5672, None,
                                           credentials)
        connection = pika.BlockingConnection(parameters)
        AcmeioFunctionalTests.channel = connection.channel()
        
    def tearDown(self):
        AcmeioFunctionalTests.channel.close()
            
    def test_post_job_and_get_status(self):
        response = self.testapp.post('/',
                {
                    'job-type':'cnx.desktop.latex.completezip',
                    'id':'col10642', 'version':'1.2', 
                    'url':'http://cnx.org', 
                    'content-url':'http://cnx.org/content/col10642/1.2/',
                    }, status=200)  
                   
        status_response = self.testapp.get(re.sub('http://localhost:6543', '', response.body), status=200)        
        status_dict = json.loads(status_response.body)
        self.assertEqual(status_dict['tasks-completed'], 0)
        self.assertEqual(status_dict['tasks-total'], 1)

        queue = 'cnx_desktop_latex_completezip'
        channel = AcmeioFunctionalTests.channel

        # Get the job from the queue that was just put there
        tag = channel.basic_get(queue=queue, no_ack=True)
        # Last element of the message is the encoded build request
        build_request = jsonpickle.decode(tag[-1])
        # Make sure the build request has the right stuff in it
        job_id = build_request.get_job_id()
        self.assertEquals(job_id, int(re.sub('http://localhost/status/', '', response.body)))
        package = build_request.get_package()
        self.assertEquals(package, 'col10642')
        version = build_request.get_version()
        self.assertEquals(version, '1.2')       

    def test_post_errors(self):
        # request is missing content
        response = self.testapp.post('/',
                {
                    'job-type':'cnx.desktop.latex.completezip', 
                    'id':'col10001', 'version':'1.1', 
                    'url':'http://cnx.org/content', 
                    }, status=400)
        # incorrect job type, creates server error
        params = {'job-type':'cnx.desktop.Purple.completezip', 
                    'id':'col10001', 'version':'1.1', 
                    'url':'http://cnx.org/content',                     
                    'content-url':'http://cnx.org/content/col10001',
                    }
        self.assertRaises(IndexError, self.testapp.post, '/', params)
                    
        # request type doesn't match one defined in acmeio, should get not found error
        response = self.testapp.get('/',
                {
                    'job-type':'cnx.desktop.latex.completezip', 
                    'id':'col10001', 'version':'1.1', 
                    'url':'http://cnx.org/content',                     
                    'content-url':'http://cnx.org/content/col10001',
                    }, status=404)