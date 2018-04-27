
![](https://www.cyberprotect.fr/wp-content/uploads/2015/12/Logo-340-156-web-noir.png)

> Rémi ALLAIN <rallain@cyberprotect.fr>

# The Hive Bee Bot 

Python script for automatically create a case in The Hive and start Cortex analyzers adapted to fit the observables.

## Fast start-up

Go into TheHiveBeeBot directory

```bash
cd TheHiveBeeBot-master
```

Launch `setup.py`

```bash
python setup.py install
```

Open `config.json` and replace the value of `api.uri.thehive` and `api.credentials.key`

Then execute `app.py`

```bash
python app.py -H 0.0.0.0 -p 9898
```

Server is now running on port 9898, you can send a submit query :

```bash
curl -X POST \
  http://127.0.0.1:9898/submit \
  -H 'Content-Type: application/json' \
  -d '
{
  "case": {
    "description": "-- test --",
    "tags": [
      "test"
    ],
    "title": "-- test --",
    "tlp": null
  },
  "jobs": {
    "scopes": [
      "local",
      "ext"
    ]
  },
  "observable": {
    "data": "./test.png",
    "dataType": "file",
    "ioc": true,
    "message": "test",
    "tags": [
      "test"
    ],
    "tlp": 2
  }
}
'
```

Go into your The Hive platform and check if a new case has been created. If not, you can refer to the errors in the response.

## Requirements

Python 2.7+

Python libraries (available via PIP) :

- magic (`pip install python-magic`)
- future (`pip install future`)
- requests (`pip install requests`)
- thehive4py (`pip install thehive4py`)
- flask (`pip install flask`)
- argparse (`pip install argparse`)

## Installation

```bash
cd TheHiveBeeBot-master
python setup.py install
```

## Configuration

Open `config.json` and replace the value of `api.uri.thehive` and `api.credentials.key`

### Matching rules

The Hive Bee Bot extends data types for greater accuracy. For example in The Hive, there is the *file* data type. In The Hive Bee Bot, you can extend the precision of this type by adding a tree structure. For example, a windows binary file will have the following types :

- *file*
- *file/binary*
- *file/binary/windows*

These subtypes are fully customizable. They are simply dependent on the rules you assign within that configuration file.

In order to assign a file type with its extended type, entries must be created in `routing`. Each entry must have at least one row in `regex` and one row in `type`. The regex field is an array containing regular expressions that will be applied to the file information. If there is a match, the file inherits the types and subtypes specified in the type field.

```json
"routing": [
    {
        "regex": [
            "ELF",
            "byte-compiled",
            "binary"
        ],
        "type": [
            "file/binary"
        ]
    }
]
```

Once you've made your routing, you can fulfill the `analyzers` fields. In this section you should list all the analyzers present in your Cortex. For each scanner, you must specify with which file types and subtypes it should be executed. Thus, when a data is submitted, the analyzers having the types and/or subtypes corresponding to the data will be selected.

```json
"analyzers": [
    {
        "id": "VirusTotal_Scan ",
        "scope": "ext",
        "cortexId": "CORTEX-SERVER-ID",
        "type": [
            "file/binary",
            "file/text",
            "url"
        ]
    }
]
```

## Usage

### API

Execute `app.py`

```bash
python app.py -H 0.0.0.0 -p 9898
```

Server is now running on port 9898, you can send a submit query :

```bash
curl -X POST \
  http://127.0.0.1:9898/submit \
  -H 'Content-Type: application/json' \
  -d '
{
  "case": {
    "description": "-- test --",
    "tags": [
      "test"
    ],
    "title": "-- test --",
    "tlp": null
  },
  "jobs": {
    "scopes": [
      "local",
      "ext"
    ]
  },
  "observable": {
    "data": "./test.png",
    "dataType": "file",
    "ioc": true,
    "message": "test",
    "tags": [
      "test"
    ],
    "tlp": 2
  }
}
'
```

### Script

First, import the library

```python
from thehivebeebot.core import TheHiveBeeBot
```

Then load your configuration

```python
beebot = TheHiveBeeBot('config.json')
```

Add observable to a new case

```python
beebot.execute({
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
```

Or add observable to an existing case

```python
beebot.execute({
    'case': {
        'id': 'SOMECASEID'
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
```