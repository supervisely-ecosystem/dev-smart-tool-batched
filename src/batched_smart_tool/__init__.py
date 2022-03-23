from supervisely.app import StateJson

from .handlers import *
from .functions import *


StateJson()['updatingMasks'] = False
StateJson()['queueIsEmpty'] = False
StateJson()['batchInUpload'] = False
StateJson()['masksOpacity'] = 50

DataJson()['newMasksAvailable'] = False

