from asgiref.sync import async_to_sync

from supervisely.app import DataJson, StateJson, LastStateJson
from smart_tool import SmartTool

import sly_globals as g


smart_tool_widgets = []

for _ in range(10):
    smart_tool_widgets.append(SmartTool(app=g.app, state=LastStateJson(), data=DataJson()))
