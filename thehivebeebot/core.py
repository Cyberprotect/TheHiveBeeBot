#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import thehive4py.api as TheHiveApi
import thehive4py.models as TheHiveModels
import magic
import time
import re
import requests
import sys
import json
import os


class TheHiveBeeBot:
    def __init__(self, jsonfile):
        self.output = {}
        self.output['case'] = None
        self.output['types'] = []
        self.output['observables'] = []
        self.output['jobs-launched'] = []
        self.output['jobs-completed'] = []
        self.output['tasks'] = []
        self.output['errors'] = []
        self.loadConfiguration(jsonfile)

    def loadConfiguration(self, jsonfile):
        jsonData = open(jsonfile).read()
        self.config = json.loads(jsonData)
        self.api = TheHiveApi.TheHiveApi(
            self.config['api']['uri']['thehive'], self.config['api']['credentials']['key'])
        return

    def execute(self, data):
        self.caseId = None
        if 'id' in data['case']:
            self.caseId = self.selectCase(data['case']['id'])
        else:
            self.caseId = self.createCase(data)
        self.observables = []
        self.observables.append(self.createObservable(data))

        if(data['observable']['dataType'] == 'file'):
            data_extend = data
            data_extend['observable']['dataType'] = 'filename'
            data_extend['observable']['data'] = os.path.basename(data_extend['observable']['data'])
            self.observables.append(self.createObservable(data_extend))

        self.analyzerScopes = self.config['jobs']['scopes']
        if('jobs' in data and 'scopes' in data['jobs']):
            self.analyzerScopes = data['jobs']['scopes']

        jobsLaunched = []

        for observable in self.observables:

            if (observable == None) or ('dataType' not in observable and 'data' not in observable and 'id' not in observable):
                self.output['errors'] += [
                    {
                        'request': {
                            'type': 'observables_iteration', 
                            'data': observable
                        }, 
                        'response': 'observable == None or a value is missing (dataType or data or id)'
                    }
                ]
                break

            if(observable['dataType'] == 'file'):
                types = self.getTypesFromFile(observable['data'])
                analyzers = self.getAnalyzersFromTypes(types)
            else:
                analyzers = self.getAnalyzersFromTypes([observable['dataType']])

            # If analyzers are empty, a task for manual investigation is create
            if(analyzers == []):
                self.output['errors'] += [
                    {
                        'request': {
                            'type': 'load_analyzers', 
                            'data': analyzers
                        }, 
                        'response': 'no analyzers found'
                    }
                ]
                
                # Send request to create a task
                response = self.api.create_case_task(self.caseId, TheHiveModels.CaseTask(
                    title='Manual investigation needed',
                    status='Waiting',
                    flag=True
                ))

                # Catch responses
                if response.status_code == 201:
                    self.output['tasks'].append(response.json())
                else:
                    self.output['errors'] += [
                        {
                            'request': {
                                'type': 'create_task', 
                                'data': 'add a task for manual investigation'
                            }, 
                            'response': response.json()
                        }
                    ]

                # Stop the execution for this observable
                break

            for analyzer in analyzers:

                # Send request
                response = self.api.run_analyzer(analyzer['cortexId'],observable['id'],analyzer['id'])
                """url = "{}/api/connector/cortex/job".format(
                    self.config['api']['uri']['thehive'])
                payload = {
                    'analyzerId': analyzer['id'],
                    'artifactId': observable['id'],
                    'cortexId': analyzer['cortexId']
                }
                headers = {
                    'Authorization': "Bearer {}".format(self.config['api']['credentials']['key']),
                    'Content-Type': "application/json",
                }
                response = requests.request(
                    "POST", url, data=json.dumps(payload), headers=headers)
                    """
                # Catch response
                if(response.status_code == 200):
                    self.output['jobs-launched'].append({
                        'analyzerId': analyzer['id'],
                        'cortexId': analyzer['cortexId'],
                        'status': response.json()['status'],
                        'jobId': response.json()['id']
                    })
                    jobsLaunched.append(response.json()['id'])
                else:
                    self.output['errors'] += [
                        {
                            'request': {
                                'type': 'run_analyzer', 
                                'data': analyzer
                            }, 
                            'response': response.json()
                        }
                    ]
                    


        jobsFinished = []
        timeout = 30
        while len(jobsLaunched) != 0:
            time.sleep(2)
            # Timeout 60sec
            timeout -= 2
            if(timeout <= 0):
                break
            for job in jobsLaunched:
                url = "{}/api/connector/cortex/job/{}".format(
                    self.config['api']['uri']['thehive'], job)
                headers = {
                    'Authorization': "Bearer {}".format(self.config['api']['credentials']['key']),
                    'Content-Type': "application/json",
                }
                response = requests.request("GET", url, headers=headers)
                if(response.status_code == 200):
                    if(response.json()['status'] in ['Success', 'Failure']):
                        jobsFinished.append(response.json())
                        jobsLaunched.remove(job)
                        self.output['jobs-completed'].append(response.json())
                        
                else:
                    self.output['errors'] += [
                        {
                            'request': {
                                'type': 'get_job', 
                                'data': {'jobId' : job}
                            }, 
                            'response': response.json()
                        }
                    ]

        
        # Report all the finished jobs with details
        #for job in jobsFinished:
            # TODO Check if there is new observable to analyze in the results
            # if yes : add new observable and launch again

        
        # Create a task to check and close the case
        response = self.api.create_case_task(self.caseId, TheHiveModels.CaseTask(
            title='Results checking',
            status='Waiting',
            flag=True
        ))

        # Catch responses
        if response.status_code == 201:
            self.output['tasks'].append(response.json())
        else:
            self.output['errors'] += [
                {
                    'request': {
                        'type': 'create_task', 
                        'data': 'add a task to check the results'
                    }, 
                    'response': response.json()
                }
            ]

        # Remove the duplicates entries in 'types'
        self.output['types'] = list(set(self.output['types']))

        return self.output

    def selectCase(self, id):
        """
        Select an existing case
        Return integer (case identifier)
        """
        # Request the api get an existing case
        response = self.api.get_case(id)

        # Catch response
        if(response.status_code == 200):
            self.output['case'] = {
                'action': 'selection',
                'id': response.json()['id']
            }
        else:
            # TODO log
            self.output['errors'] += [
                {
                    'request': {
                        'type': 'get_case', 
                        'data': id
                    }, 
                    'response': response.json()
                }
            ]
            sys.exit(0)
        # Return case id
        return self.output['case']['id']

    def createCase(self, data):
        """
        Create a new case.
        Return integer (case identifier).
        """
        # Check the structure of data
        if('case' not in data):
            # TODO log
            sys.exit(0)
        if('title' not in data['case']):
            # TODO log
            data['case']['title'] = ''
        if('description' not in data['case']):
            # TODO log
            data['case']['description'] = ''
        if('tlp' not in data['case']):
            # TODO log
            data['case']['tlp'] = None

        # Create a new case model
        case = TheHiveModels.Case(
            title=data['case']['title'],
            description=data['case']['description'],
            tlp=data['case']['tlp'],
            tags=data['case']['tags']
        )

        # Send request
        response = self.api.create_case(case)

        # Catch response
        if response.status_code == 201:
            self.output['case'] = {
                'action': 'creation',
                'id': response.json()['id']
            }
        else:
            # TODO log
            self.output['errors'] += [
                {
                    'request': {
                        'type': 'create_case', 
                        'data': data['case']
                    }, 
                    'response': response.json()
                }
            ]
            sys.exit(0)

        # Return case id
        return self.output['case']['id']

    def createObservable(self, data):
        """
        Create a new observable.
        Return collection (observable information).
        """

        observable = None

        observableModel = TheHiveModels.CaseObservable(
            dataType=data['observable']['dataType'],
            data=[
                data['observable']['data']
            ],
            tlp=data['observable']['tlp'],
            ioc=data['observable']['ioc'],
            tags=data['observable']['tags'],
            message=data['observable']['message']
        )

        # Send request
        response = self.api.create_case_observable(self.caseId, observableModel)

        # Catch response
        if response.status_code == 201:
            observable = response.json()
            observable['data'] = data['observable']['data']
            self.output['observables'].append(observable)
        else:
            # TODO log
            self.output['errors'] += [
                {
                    'request': {
                        'type': 'create_case_observable', 
                        'data': data['observable']
                    }, 
                    'response': response.json()
                }
            ]

        # Return complete observable
        return observable

    def getTypesFromFile(self, file):
        """
        Get the extended data types from a given file.
        Return list (extended data types).
        """
        # Initalize the type list
        types = []
        # Retrieve the file information
        file_info = magic.from_file(file)

        # Match the file information with routes
        for route in self.config['routing']:
            for regex in route['regex']:
                test = re.compile(regex)
                if(test.search(file_info)):
                    # If there is a match, add the type to the return var
                    types += route['type']
        # Remove the duplicate type
        types = list(set(types))
        return types

    def getAnalyzersFromTypes(self, types):
        """
        Get the analyzers from list of data types
        Return list (analyzers information : {id, scope, cortexId})
        """
        # New way to do it :
        analyzers = []
        # For each type previously found get the analyzers with the correct scope
        for analyzer in self.config['analyzers']:
            for type in types:
                self.output['types'].append(type)
                if(type in analyzer['type'] and analyzer['scope'] in self.analyzerScopes):
                    analyzers += [{
                        'id': analyzer['id'],
                        'scope': analyzer['scope'],
                        'cortexId': analyzer['cortexId']
                    }]
        # Remove the duplicates
        analyzers = map(dict, set(tuple(sorted(d.items())) for d in analyzers))
        return analyzers
