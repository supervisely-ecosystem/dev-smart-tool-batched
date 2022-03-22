from supervisely.app import StateJson, DataJson

# from .handlers import *
from .functions import *
from .local_widgets import *


StateJson()['selectClassVisible'] = False
StateJson()['outputClassName'] = None
StateJson()['updatingClass'] = False

StateJson()['queueMode'] = 'objects'

DataJson()['objectsLeftTotal'] = 0
DataJson()['objectsLeftQueue'] = 0

