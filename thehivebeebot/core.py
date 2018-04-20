#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from thehive4py.api import TheHiveApi
from thehive4py.models import Case, CaseObservable, CaseTask
import magic,time,re,requests,sys,json,os

class TheHiveBeeBot:
    def __init__(self, jsonfile):
        self.loadConfiguration(jsonfile)
    
    def loadConfiguration(self, jsonfile):
        jsonData=open(jsonfile).read()
        self.config = json.loads(jsonData)
        self.api = TheHiveApi(self.config['api']['uri']['thehive'], self.config['api']['credentials']['key'])
        return

    def execute(self, data):
        self.caseId = None
        if 'id' in data['case']:
            self.caseId = self.selectCase(data['case']['id'])
        else:
            self.caseId = self.createCase(data)
        self.observables = []
        self.observables.append(self.createObservable(data))

        if(data['observable']['dataType']=='file'):
            data_extend = data
            data_extend['observable']['dataType'] = 'filename'
            data_extend['observable']['data'] = os.path.basename(data_extend['observable']['data'])
            self.observables.append(self.createObservable(data_extend))

        self.analyzerScopes = self.config['jobs']['scopes']
        if('jobs' in data and 'scopes' in data['jobs']):
            self.analyzerScopes = data['jobs']['scopes']

        jobsLaunched = []

        for observable in self.observables:

            if (observable==None) or ('dataType' not in observable and 'data' not in observable and 'id' not in observable):
                #TODO error message
                break

            print('-----------------')
            print('Select analyzers for {} {}'.format(observable['dataType'], observable['id']))
            print('-----------------')

            if(observable['dataType']=='file'):
                types = self.getTypesFromFile(observable['data'])
                analyzers = self.getAnalyzersFromTypes(types)
            else:
                analyzers = self.getAnalyzersFromTypes([observable['dataType']])

            if(analyzers == []):
                #TODO error message and maybe a task to manually investigate ?
                print('No analyzers found')
                print('Add a task for manual investigation')
                response = self.api.create_case_task(self.caseId, CaseTask(
                    title='Manual investigation needed',
                    status='Waiting',
                    flag=True
                ))
                if response.status_code == 201:
                    print('Task id : {}'.format(response.json()['id']))
                else:
                    msgError = 'Unknown error'
                    if('message' in response.json()):
                        msgError = response.json()['message'].encode('utf-8')
                    print('Error while creating task : {}'.format(msgError.replace('\n', '')))
                break

            print('-----------------')
            print('Create jobs for {} {}'.format(observable['dataType'], observable['id']))
            print('-----------------')

            
            for analyzer in analyzers:
                #TODO replace all the code below with this :
                #self.api.run_analyzer(analyzer['cortexId'],observable['id'],analyzer['id'])
                url = "{}/api/connector/cortex/job".format(self.config['api']['uri']['thehive'])
                payload = {
                    'analyzerId': analyzer['id'],
                    'artifactId': observable['id'],
                    'cortexId': analyzer['cortexId']
                }
                headers = {
                    'Authorization': "Bearer {}".format(self.config['api']['credentials']['key']),
                    'Content-Type': "application/json",
                }
                response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
                if(response.status_code==200):
                    print('{} ({}) : {} {}'.format(analyzer['id'], analyzer['cortexId'], response.json()['status'], response.json()['id']))
                    jobsLaunched.append(response.json()['id'])
                else:
                    msgError = 'Unknown error'
                    if('message' in response.json()):
                        msgError = response.json()['message'].encode('utf-8')
                    print('{} ({}) : {}'.format(analyzer['id'], analyzer['cortexId'], msgError.replace('\n', '')))


        print('-----------------')
        print('Jobs completed')
        print('-----------------')

        jobsFinished = []
        while len(jobsLaunched) != 0:
            time.sleep(2)
            for job in jobsLaunched:
                url = "{}/api/connector/cortex/job/{}".format(self.config['api']['uri']['thehive'], job)
                headers = {
                    'Authorization': "Bearer {}".format(self.config['api']['credentials']['key']),
                    'Content-Type': "application/json",
                }
                response = requests.request("GET", url, headers=headers)
                if(response.status_code==200):
                    if(response.json()['status'] in ['Success', 'Failure']):
                        jobsFinished.append(response.json())
                        jobsLaunched.remove(job)
                        print('Job {} {} on {} for artifact {}'.format(job, response.json()['status'], response.json()['cortexId'], response.json()['artifactId']))
                else:
                    jobsLaunched.remove(job)
                    msgError = 'Unknown error'
                    if('message' in response.json()):
                        msgError = response.json()['message']
                    print('Job {} Error : {}'.format(job, msgError))
            
        print('-----------------')
        print('Analysis results')
        print('-----------------')
        # Report all the finished jobs with details
        for job in jobsFinished:
            print('*******')
            print('{} on {} for artifact {}'.format(job['analyzerId'], job['cortexId'], job['artifactId']))
            print(json.dumps(job['report']['full'], indent=4))
            print('*******')
            #TODO Check if there is new observable to analyze in the results
            # if yes : add new observable and launch again

        print('-----------------')
        print('End')
        print('-----------------')
        # Create a task to check and close the case
        print('Add a task for check and close the case')
        response = self.api.create_case_task(self.caseId, CaseTask(
            title='Results checking',
            status='Waiting',
            flag=True
        ))
        if response.status_code == 201:
            print('Task id : {}'.format(response.json()['id']))
        else:
            msgError = 'Unknown error'
            if('message' in response.json()):
                msgError = response.json()['message'].encode('utf-8')
            print('Error while creating task : {}'.format(msgError.replace('\n', '')))

        return

    def selectCase(self, id):
        print('-----------------')
        print('Select case {}'.format(id))
        print('-----------------')
        url = "{}/api/case/{}".format(self.config['api']['uri']['thehive'], id)
        headers = {
            'Authorization': "Bearer {}".format(self.config['api']['credentials']['key']),
            'Content-Type': "application/json",
        }
        response = requests.request("GET", url, headers=headers)
        if(response.status_code==200):
            print('case id : {}'.format(response.json()['id']))
            print('case number : {}'.format(response.json()['caseId']))
        else:
            msgError = 'Unknown error'
            if('message' in response.json()):
                msgError = response.json()['message']
            print('Case not found : {}'.format(msgError))
            sys.exit(0)
        return response.json()['id']



    def createCase(self, data):
        print('-----------------')
        print('Create case')
        print('-----------------')
        case = Case(title=data['case']['title'], description=data['case']['description'], tlp=data['case']['tlp'], tags=data['case']['tags'])

        response = self.api.create_case(case)
        if response.status_code == 201:
            print('case id : {}'.format(response.json()['id']))
            print('case number : {}'.format(response.json()['caseId']))
            id = response.json()['id']
        else:
            print(response.json()['message'])
            sys.exit(0)
        return id

    def createObservable(self, data):
        print('-----------------')
        print('Create observable')
        print('-----------------')
        print('Data type : {}'.format(data['observable']['dataType']))
        domain = CaseObservable(dataType=data['observable']['dataType'],
                                data=[data['observable']['data']],
                                tlp=data['observable']['tlp'],
                                ioc=data['observable']['ioc'],
                                tags=data['observable']['tags'],
                                message=data['observable']['message']
                                )
        response = self.api.create_case_observable(self.caseId, domain)
        if response.status_code == 201:
            print('Observable id : {}'.format(response.json()['id']))
            observable = response.json()
            observable['data'] = data['observable']['data']
            return observable
        else:
            print(response.json()['message'])
            return None
        

    def getTypesFromFile(self, file):
        # Initalize the type list
        types = []
        # Retrieve the file information
        file_info = magic.from_file(file)
        print('File info result : {}'.format(file_info))
        # Match the file information with routes
        for route in self.config['routing']:
            for regex in route['regex']:
                test = re.compile(regex)
                if(test.search(file_info)):
                    # If there is a match, add the type to the return var
                    print('Type found : {}'.format(', '.join(route['type'])))
                    types += route['type']
        # Remove the duplicate type
        types = list(set(types))
        return types

    def getAnalyzersFromTypes(self, types):
        # New way to do it :
        analyzers = []
        # For each type previously found get the analyzers with the correct scope
        for analyzer in self.config['analyzers']:
            for type in types:
                if(type in analyzer['type'] and analyzer['scope'] in self.analyzerScopes):
                    analyzers += [{
                        'id': analyzer['id'],
                        'scope': analyzer['scope'],
                        'cortexId': analyzer['cortexId']
                    }]
                    print('Load {} ({}) on {}'.format(analyzer['id'], analyzer['scope'], analyzer['cortexId']))
        # Remove the duplicates
        analyzers = map(dict, set(tuple(sorted(d.items())) for d in analyzers))
        return analyzers


