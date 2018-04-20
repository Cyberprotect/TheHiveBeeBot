#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, sys, os
from thehivebeebot.core import TheHiveBeeBot

thbb = TheHiveBeeBot('{}/thehivebeebot.json'.format(os.path.dirname(os.path.realpath(__file__))))

thbb.execute({
    'case': {
        'title': '-- test --',
        'description': '-- test --',
        'tlp': None,
        'tags': ['test']
    },
    'observable': {
        'dataType': 'file',
        'data': 'test.png',
        'tlp': 2,
        'ioc': True,
        'message': 'test',
        'tags': ['test']
    },
    'jobs': {
        'scopes': [
            'local',
            'ext'
        ]
    }
})
