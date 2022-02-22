from supervisely.app import StateJson, DataJson

from .handlers import *
from .functions import *

StateJson()['currentStep'] = 0

StateJson()['inputProject'] = {
    'id': None,
    'loading': False
}

StateJson()['outputProject'] = {
    'id': None,
    'mode': 'new',
    'name': None,
    'loading': False
}

StateJson()['outputClass'] = {
    'mode': 'new',
    'name': None
}

StateJson()['processingServerSessionId'] = None

StateJson()['selectProjectLoading'] = None

DataJson()['connectorOptions'] = {
    "sessionTags": ["sly_smart_annotation"],
    "showLabel": False,
    "size": "small"
}

