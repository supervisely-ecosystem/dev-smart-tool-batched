from asgiref.sync import async_to_sync

from supervisely.app import DataJson, StateJson, LastStateJson
from smart_tool import SmartTool

import sly_globals as g


class GridController:
    def __init__(self, origin_widget_class):
        self._origin_widget_class = origin_widget_class
        self.widgets = {}

    def change_count(self, actual_count, app, state, data):
        while actual_count > len(self.widgets):
            self._add(app, state, data)

        while actual_count < len(self.widgets):
            self._remove(app, state, data)

    def get_widget_by_id(self, widget_id):
        return self.widgets[widget_id]

    def update_local_fields(self, state, data):
        for widget in self.widgets.values():
            widget.update_local_fields(state=state, data=data)

    def update_remote_fields(self, state, data):
        for widget in self.widgets.values():
            widget.update_remote_fields(state=state, data=data)

    def _add(self, app, state, data):
        widget = self._origin_widget_class(app, state, data)

        if not g.bboxes_to_process.empty():
            new_data = g.bboxes_to_process.get()
            widget.update_fields_by_data(new_data)

        self.widgets[widget.identifier] = widget

    def _remove(self, app, state, data):
        identifiers = list(self.widgets.keys())
        if len(identifiers) > 0:
            last_object = self.widgets.pop(identifiers[-1])
            g.bboxes_to_process.queue.appendleft(last_object.get_data_to_send())
            last_object.remove_remote_fields(state=state, data=data)



