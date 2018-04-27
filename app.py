#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from thehivebeebot.core import TheHiveBeeBot
import json, os, sys, argparse

parser = argparse.ArgumentParser(description='Script for automatically create a case in The Hive and start Cortex analyzers adapted to fit the observables.')
parser.add_argument('-H','--host', help='Server ip', default='0.0.0.0')
parser.add_argument('-p','--port', help='Server port', default='9898')
args = vars(parser.parse_args())

app = Flask(__name__)

@app.route('/', methods=['post','get','delete','put','options','patch'])
def index():
    return jsonify({
        'app':'thehivebeebot', 
        'status':'running'}
    )

@app.route('/submit', methods=['post'])
def submit():
    core = TheHiveBeeBot('{}/config.json'.format(os.path.dirname(os.path.realpath(__file__))))
    return jsonify(core.execute(json.loads(request.get_data())))

app.run(host=args['host'], port=args['port'])