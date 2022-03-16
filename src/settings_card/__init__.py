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
    'name': f'{g.api.project.get_info_by_id(g.input_project_id).name}_BST',
    'loading': False,
    'dialogVisible': False
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


