from loguru import logger


class GridController:
    def __init__(self, origin_widget_class):
        self._origin_widget_class = origin_widget_class
        self.widgets = {}

    def change_count(self, actual_count, app, state, data, images_queue):
        while actual_count > len(self.widgets) and not images_queue.empty():
            self._add(app, state, data, images_queue)

        while actual_count < len(self.widgets):
            self._remove(state, data, images_queue)

    def change_padding(self, actual_padding):
        for widget in self.widgets.values():
            if not widget.is_empty:
                widget.add_bbox_padding(padding_coefficient=actual_padding)

    def get_widget_by_id(self, widget_id):
        return self.widgets[widget_id]

    def update_local_fields(self, state, data):
        for widget in self.widgets.values():
            widget.update_local_fields(state=state, data=data)

    def update_remote_fields(self, state, data):
        for widget in self.widgets.values():
            widget.update_remote_fields(state=state, data=data)

    def _add(self, app, state, data, images_queue):
        widget = self._origin_widget_class(app, state, data)
        widget.is_active = False

        if not images_queue.empty():
            widget.is_active = True
            new_data = images_queue.get()
            widget.update_fields_by_data(new_data)
            if not widget.is_empty:
                widget.add_bbox_padding(padding_coefficient=state['bboxesPadding'])

        self.widgets[widget.identifier] = widget

    def _remove(self, state, data, images_queue):
        identifiers = list(self.widgets.keys())
        if len(identifiers) > 0:
            last_object = self.widgets.pop(identifiers[-1])

            if images_queue is not None:
                images_queue.queue.appendleft(last_object.get_data_to_send())

            last_object.remove_remote_fields(state=state, data=data)

    def clean_all(self, state, data, images_queue=None):
        identifiers = list(self.widgets.keys())
        while len(identifiers) > 0:
            self._remove(state, data, images_queue)
            identifiers = list(self.widgets.keys())
