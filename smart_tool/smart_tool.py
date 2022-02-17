import asyncio
import copy
import functools
import re
import uuid
from pathlib import Path
from uuid import uuid4

import markupsafe
from asgiref.sync import async_to_sync
from jinja2 import Environment

from supervisely.app import StateJson, LastStateJson, DataJson
from supervisely.app.jinja2 import create_env


def get_existing_point_index(existing_points, connected_point_id):
    for index, exising_point in enumerate(existing_points):
        if exising_point['id'] == connected_point_id:
            return index


class SmartTool:
    def __init__(self, app, state, data):
        self.app = app
        self.identifier = self.get_widget_identifier(state, data)

        self.image_url = None
        self.image_hash = None
        self.positive_points = []
        self.negative_points = []
        self.bbox = []
        self.mask = None
        self.is_active = True

        self._connected_points = list()  # [{1, 2, 3), {4, 5, 6}] — connected points

        self.update_remote_fields(state, data)

        self.needs_an_update = False

    def get_updated_points(self, state, data, points_type='positive'):
        new_widget_data = self.get_widget_data_from_remote(state=state, data=data)

        if new_widget_data is not None:
            last_points_coordinates = [tuple(point['position'][0]) for point in
                                       self.__getattribute__(f'{points_type}_points')]
            new_points_coordinates = [tuple(point['position'][0]) for point in new_widget_data[f'{points_type}Points']]

            updated_points = list(set(new_points_coordinates) - set(last_points_coordinates))

            return [point for point in new_widget_data[f'{points_type}Points'] if
                    tuple(point['position'][0]) in updated_points]

        return []

    def get_removed_points(self, state, data, points_type):
        new_widget_data = self.get_widget_data_from_remote(state=state, data=data)

        if new_widget_data is not None:
            last_points_coordinates = [str(point['id']) for point in
                                       self.__getattribute__(f'{points_type}_points')]
            new_points_coordinates = [str(point['id']) for point in new_widget_data[f'{points_type}Points']]

            removed_points = list(set(last_points_coordinates) - set(new_points_coordinates))

            return [point for point in self.__getattribute__(f'{points_type}_points') if
                    str(point['id']) in removed_points]

        return []

    def get_box_size(self):
        box_width = self.bbox[1][0] - self.bbox[0][0]
        box_height = self.bbox[1][1] - self.bbox[0][1]

        return box_width, box_height

    def get_relative_coordinates(self, abs_coordinates):
        box_width, box_height = self.get_box_size()
        return {
            'x': (abs_coordinates['position'][0][0] - self.bbox[0][0]) / box_width,
            'y': (abs_coordinates['position'][0][1] - self.bbox[0][1]) / box_height,
        }

    def add_connected_point(self, connected_points_ids):
        self._connected_points.append(connected_points_ids)

    def update_by_relative_coordinates(self, updated_point, points_type='positive'):
        self.needs_an_update = True

        box_width, box_height = self.get_box_size()
        x_real = int(updated_point['relative']['x'] * box_width + self.bbox[0][0])
        y_real = int(updated_point['relative']['y'] * box_height + self.bbox[0][1])

        existing_points = self.__getattribute__(f'{points_type}_points')
        existing_points_ids = [point['id'] for point in existing_points]

        for connected_points in self._connected_points:
            if updated_point['id'] in connected_points and len(set(existing_points_ids).intersection(connected_points)) > 0:  # change existing point
                connected_point_id = list(set(existing_points_ids).intersection(connected_points))[0]
                index = existing_points_ids.index(connected_point_id)
                existing_points[index]['position'] = [[x_real, y_real]]
                break

        else:  # create new point
            point_id = f'{uuid.uuid4()}'
            existing_points.append({'position': [[x_real, y_real]], 'id': point_id})

            return point_id

    def remove_connected_point(self, removed_point, points_type='positive'):
        existing_points = self.__getattribute__(f'{points_type}_points')
        existing_points_ids = [point['id'] for point in existing_points]

        for connected_points_index, connected_points in enumerate(self._connected_points):  # change existing point
            if removed_point['id'] in connected_points and len(set(existing_points_ids).intersection(connected_points)) > 0:
                connected_point_id = list(set(existing_points_ids).intersection(connected_points))[0]
                index = existing_points_ids.index(connected_point_id)

                existing_points.pop(index)
                self._connected_points.pop(connected_points_index)

                break

    def clean_points(self):
        self.positive_points = []
        self.negative_points = []
        self._connected_points = []

    # @TODO: move next methods to Factory Class

    def get_widget_data_from_remote(self, state, data):
        new_widgets = state["widgets"].get(f'{self.__class__.__name__}', {})  # get widget_data from state
        return new_widgets.get(self.identifier)

    def update_local_fields(self, state, data):
        new_widget_data = self.get_widget_data_from_remote(state=state, data=data)
        self.update_fields_by_data(new_widget_data)

    def update_fields_by_data(self, new_widget_data):
        self.image_url = new_widget_data.get('imageUrl', '')
        self.image_hash = new_widget_data.get('imageHash', '')
        self.positive_points = new_widget_data.get('positivePoints', [])
        self.negative_points = new_widget_data.get('negativePoints', [])
        self.bbox = new_widget_data.get('bbox', [])
        self.mask = new_widget_data.get('mask', None)
        self.is_active = new_widget_data.get('isActive', True)

    def get_data_to_send(self):
        return {
            'identifier': f'{self.identifier}',
            'imageUrl': self.image_url,
            'imageHash': self.image_hash,
            'positivePoints': self.positive_points,
            'negativePoints': self.negative_points,
            'bbox': self.bbox,
            'mask': self.mask,
            'isActive': self.is_active
        }

    def update_remote_fields(self, state, data):
        state['widgets'].setdefault(f'{self.__class__.__name__}', {})[f'{self.identifier}'] = self.get_data_to_send()
        async_to_sync(state.synchronize_changes)()

    def remove_remote_fields(self, state, data):
        existing_objects = state['widgets'].get(f'{self.__class__.__name__}', {})
        if existing_objects.get(self.identifier, None) is not None:
            existing_objects.pop(self.identifier)
            async_to_sync(state.synchronize_changes)()

    def get_widget_identifier(self, state, data):
        existing_widgets_count = len(state["widgets"].get(f'{self.__class__.__name__}', []))
        return f'{existing_widgets_count:04d}'

    def to_html(self):
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)

        html = jinja2_sly_env.get_template("smart_tool.html").render(identifier=self.identifier)
        return markupsafe.Markup(html)

    @staticmethod
    def to_undefined_html():
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)

        html = jinja2_sly_env.get_template("smart_tool.html").render()
        return markupsafe.Markup(html)
