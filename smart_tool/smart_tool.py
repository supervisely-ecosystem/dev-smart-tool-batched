import asyncio
import copy
import functools
import re
import uuid
from pathlib import Path
from uuid import uuid4

import markupsafe
from supervisely.app.fastapi import run_sync
from jinja2 import Environment

from supervisely.app import StateJson, DataJson
from supervisely.app.jinja2 import create_env


def get_existing_point_index(existing_points, connected_point_id):
    for index, exising_point in enumerate(existing_points):
        if exising_point['id'] == connected_point_id:
            return index


class SmartTool:
    def __init__(self, app, state, data):
        self.app = app
        self.identifier = self.get_widget_identifier(state, data)

        self.image_link = None
        self.image_remote_link = None
        self.image_id = None

        self.image_name = None
        self.sly_id = None

        self.image_url = None
        self.image_hash = None
        self.image_size = None

        self.dataset_name = None

        self.positive_points = []
        self.negative_points = []

        self.original_bbox = []
        self.scaled_bbox = []

        self.mask = None
        self.maskOpacity = 50
        self.needs_an_update = False

        self.is_active = True
        self.is_broken = False
        self.is_finished = False

        self.last_call = 0

        self._connected_points = list()  # [{1, 2, 3), {4, 5, 6}] — connected points

        self.update_remote_fields(state, data)


    @property
    def is_empty(self):
        if len(self.original_bbox) > 0:
            return False
        return True

    def get_updated_points(self, state, data, points_type='positive'):
        new_widget_data = self.get_widget_data_from_remote(state=state, data=data)

        if new_widget_data is not None:
            last_points_coordinates = [tuple(point['position'][0]) for point in self.__getattribute__(f'{points_type}_points')]
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

    def get_bbox_size(self, current_bbox):
        box_width = current_bbox[1][0] - current_bbox[0][0]
        box_height = current_bbox[1][1] - current_bbox[0][1]
        return box_width, box_height

    def add_bbox_padding(self, padding_coefficient=0):
        padding_coefficient /= 100

        original_w, original_h = self.get_bbox_size(current_bbox=self.original_bbox)
        additional_w, additional_h = int(original_w * padding_coefficient // 2), int(original_h * padding_coefficient // 2),

        self.scaled_bbox[0][0] = self.original_bbox[0][0] - additional_w if self.original_bbox[0][0] - additional_w > 0 else 0
        self.scaled_bbox[0][1] = self.original_bbox[0][1] - additional_h if self.original_bbox[0][1] - additional_h > 0 else 0
        self.scaled_bbox[1][0] = self.original_bbox[1][0] + additional_w if self.original_bbox[1][0] + additional_w < self.image_size[0] else self.image_size[0] - 1
        self.scaled_bbox[1][1] = self.original_bbox[1][1] + additional_h if self.original_bbox[1][1] + additional_h < self.image_size[1] else self.image_size[1] - 1

    def change_mask_opacity(self, opacity_coefficient):
        # if self.mask is not None:
        self.maskOpacity = opacity_coefficient

    def get_relative_coordinates(self, abs_coordinates):
        box_width, box_height = self.get_bbox_size(current_bbox=self.scaled_bbox)
        return {
            'x': (abs_coordinates['position'][0][0] - self.scaled_bbox[0][0]) / box_width,
            'y': (abs_coordinates['position'][0][1] - self.scaled_bbox[0][1]) / box_height,
        }

    def add_connected_point(self, connected_points_ids):
        self._connected_points.append(connected_points_ids)

    def update_by_relative_coordinates(self, updated_point, points_type='positive'):
        self.needs_an_update = True

        box_width, box_height = self.get_bbox_size(current_bbox=self.scaled_bbox)
        x_real = int(updated_point['relative']['x'] * box_width + self.scaled_bbox[0][0])
        y_real = int(updated_point['relative']['y'] * box_height + self.scaled_bbox[0][1])

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

    def remove_contour(self):
        if self.mask is not None:
            self.mask['contour'] = None

    def _remove_repeated_points(self, points_list):
        points = {}
        for point in points_list:
            point_id = point['id']
            if points.get(point_id) is None:
                points[point_id] = point

        return list(points.values())

    def clean_up(self):
        self.positive_points = []
        self.negative_points = []
        self._connected_points = []

        self.mask = None

    # @TODO: move next methods to Parent Class

    def get_widget_data_from_remote(self, state, data):
        new_widgets = state["widgets"].get(f'{self.__class__.__name__}', {})  # get widget_data from state
        return new_widgets.get(self.identifier)

    def update_local_fields(self, state, data):
        new_widget_data = self.get_widget_data_from_remote(state=state, data=data)
        self.update_fields_by_data(new_widget_data)

    def update_fields_by_data(self, new_widget_data):
        self.image_link = new_widget_data.get('imageLink', '')
        self.image_url = new_widget_data.get('imageUrl', '')

        # # ! only for local debug
        # if not self.image_url.startswith('https://dev.supervise.ly'):
        #     # * .com will not work
        #     self.image_url = "https://dev.internal.supervisely.com" + new_widget_data.get('imageUrl', '')

        self.image_hash = new_widget_data.get('imageHash', '')
        self.image_remote_link = new_widget_data.get('imageRemoteLink')
        self.image_id = new_widget_data.get('imageId')
        self.image_name = new_widget_data.get('imageName', '')
        self.image_size = new_widget_data.get('imageSize', '')
        self.dataset_name = new_widget_data.get('datasetName', '')
        self.positive_points = self._remove_repeated_points(new_widget_data.get('positivePoints', []))
        self.negative_points = self._remove_repeated_points(new_widget_data.get('negativePoints', []))
        self.original_bbox = new_widget_data.get('originalBbox', [])
        self.scaled_bbox = new_widget_data.get('scaledBbox', [])
        self.mask = new_widget_data.get('mask', None)
        self.sly_id = new_widget_data.get('slyId', True)
        self.needs_an_update = new_widget_data.get('needsAnUpdate', False)

        self.is_active = new_widget_data.get('isActive', True)
        self.is_broken = new_widget_data.get('isBroken', False)
        self.is_finished = new_widget_data.get('isFinished', False)

        self.last_call = new_widget_data.get('lastCall', 0)

    def get_data_to_send(self):
        return {
            'identifier': f'{self.identifier}',
            'imageLink': self.image_link,
            'imageUrl': self.image_url,
            'imageHash': self.image_hash,
            'imageName': self.image_name,
            'imageSize': self.image_size,
            'datasetName': self.dataset_name,
            'positivePoints': self.positive_points,
            'negativePoints': self.negative_points,
            'originalBbox': self.original_bbox,
            'scaledBbox': self.scaled_bbox,
            'mask': self.mask,
            'slyId': self.sly_id,
            'needsAnUpdate': self.needs_an_update,
            'isActive': self.is_active,
            'isBroken': self.is_broken,
            'isFinished': self.is_finished,
            'lastCall': self.last_call,
            'imageId': self.image_id,
            'imageRemoteLink': self.image_remote_link
        }

    def update_remote_fields(self, state, data, synchronize=True):
        state['widgets'].setdefault(f'{self.__class__.__name__}', {})[f'{self.identifier}'] = self.get_data_to_send()
        if synchronize:
            run_sync(state.synchronize_changes())

    def remove_remote_fields(self, state, data):
        existing_objects = state['widgets'].get(f'{self.__class__.__name__}', {})
        if existing_objects.get(self.identifier, None) is not None:
            existing_objects.pop(self.identifier)
            # run_sync(state.synchronize_changes())

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
