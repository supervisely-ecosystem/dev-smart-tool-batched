from supervisely.app import DataJson, StateJson
from .local_widgets import *
from .handlers import *


StateJson()['dialogWindow'] = {
    'mode': 'inputProject',  # can be 'bboxesOrder', 'inputProject', 'outputProject', 'modelConnection'
}


StateJson()['dialogWindowUnsavedMasks'] = False
