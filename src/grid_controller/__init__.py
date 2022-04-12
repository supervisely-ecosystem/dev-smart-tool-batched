from supervisely.app import StateJson

from .classes import *
from .handlers import *

StateJson()['windowsCount'] = 12
StateJson()['toolSize'] = 16
StateJson()['bboxesPadding'] = 50
