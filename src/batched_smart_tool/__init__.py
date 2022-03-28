from supervisely.app import StateJson

from .handlers import *
from .functions import *


StateJson()['updatingMasks'] = False
StateJson()['queueIsEmpty'] = False
StateJson()['batchInUpload'] = False
StateJson()['masksOpacity'] = 50

StateJson()['bboxesOrder'] = 'images'  # sizes
StateJson()['bboxesOrderLoading'] = False

DataJson()['newMasksAvailable'] = False


