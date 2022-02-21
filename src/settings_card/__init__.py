from supervisely.app import StateJson, DataJson

from .handlers import *
from .functions import *

StateJson()['inputProjectId'] = None
StateJson()['outputProjectId'] = None

StateJson()['selectedClassName'] = None
StateJson()['processingServerSessionId'] = None

StateJson()['selectProjectLoading'] = None

DataJson()['connectorOptions'] = {
    "sessionTags": [],
    "showLabel": False,
    "size": "small"
}
