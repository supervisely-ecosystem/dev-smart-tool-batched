from asgiref.sync import async_to_sync

from supervisely.app import DataJson, StateJson, LastStateJson
from smart_tool import SmartTool

import sly_globals as g


class GridController:
    def __init__(self, origin_widget_class):
        self._origin_widget_class = origin_widget_class
        self.created_widgets = []

    def change_count(self, actual_count, app, state, data):
        while actual_count > len(self.created_widgets):
            self._add(app, state, data)

        while actual_count < len(self.created_widgets):
            self._remove(app, state, data)

    def _add(self, app, state, data):
        self.created_widgets.append(self._origin_widget_class(app, state, data))

    def _remove(self, app, state, data):
        if len(self.created_widgets) > 0:
            last_object = self.created_widgets.pop()
            last_object.remove_remote_fields(state=state, data=data)



