from supervisely.app import DataJson, StateJson
from .local_widgets import *
from .handlers import *


StateJson()['dialogWindow'] = {
    'mode': None,  # can be 'outputProject', 'modelConnection', 'unsavedMasks'
}

