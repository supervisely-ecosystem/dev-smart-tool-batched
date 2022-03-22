from supervisely.app import StateJson

from .handlers import *
from .functions import *


StateJson()['updatingMasks'] = False
StateJson()['queueIsEmpty'] = False
StateJson()['batchInUpload'] = False


DataJson()['newMasksAvailable'] = False
