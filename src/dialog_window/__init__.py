from supervisely.app import DataJson, StateJson
from .local_widgets import *
from .handlers import *


StateJson()['dialogWindow'] = {
    'mode': 'inputProject',  # can be 'inputProject', 'outputProject', 'modelConnection', 'unsavedMasks'
}


StateJson()['dialogWindowUnsavedMasks'] = False
