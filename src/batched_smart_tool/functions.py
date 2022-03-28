import copy
import json

import imutils as imutils
import numpy as np

import smart_tool
import src.sly_globals as g
import supervisely

import cv2

from supervisely.app import DataJson

from loguru import logger


def update_single_widget_realtime(widget_id, state):
    widget = g.grid_controller.get_widget_by_id(widget_id=widget_id)

    try:
        data_to_process = get_data_from_widget_to_compute_masks(widget)

        response_data = g.api.task.send_request(int(state['processingServer']['sessionId']), "smart_segmentation",
                                                data={},
                                                context=data_to_process, timeout=60)

        if response_data.get('origin') is not None:
            set_widget_mask_by_data(widget, response_data, state=state)
            widget.needs_an_update = False
        else:
            widget.mask = None
    except Exception as ex:
        logger.warning(f'{ex}')

    widget.update_remote_fields(state=state, data=DataJson())


def new_masks_available_flag():
    for widget in g.grid_controller.widgets.values():
        if widget.needs_an_update:
            return True
    return False


def get_contours(base64mask, origin_shift):
    test_mask = np.asarray(supervisely.Bitmap.base64_2_data(base64mask)).astype(np.uint8) * 255
    thresholded_mask = cv2.threshold(test_mask, 100, 255, cv2.THRESH_BINARY)[1]

    contours = cv2.findContours(thresholded_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    reshaped_contours = []
    for contour in contours:
        reshaped_contour = contour.reshape(contour.shape[0], 2)

        reshaped_contour[:, 0] += origin_shift['x']
        reshaped_contour[:, 1] += origin_shift['y']

        reshaped_contours.append(reshaped_contour.tolist())

    return reshaped_contours


def set_widget_mask_by_data(widget: smart_tool.SmartTool, data, state):
    contours = copy.deepcopy(get_contours(data['bitmap'], data['origin']))

    # widget.remove_contour()
    # widget.update_remote_fields(state=state, data=DataJson())

    widget.mask = {
        'data': data.get('bitmap'),
        'origin': [data['origin']['x'], data['origin']['y']],
        'color': '#77e377',
        'contour': contours
    }


def update_local_masks(response, state):
    for index, widget in enumerate(g.grid_controller.widgets.values()):
        data = response.get(f'{index}')
        if data is not None:
            set_widget_mask_by_data(widget, data, state)


def add_point_to_active_cards(origin_identifier, updated_point, points_type):
    new_connected_points = set()

    for widget in g.grid_controller.widgets.values():
        if widget.is_active and widget.identifier != origin_identifier and not widget.is_empty:
            point_id = widget.update_by_relative_coordinates(updated_point, points_type)

            if point_id is not None:
                new_connected_points.add(point_id)

    new_connected_points.add(updated_point['id'])

    for widget in g.grid_controller.widgets.values():
        if widget.is_active:
            widget.add_connected_point(connected_points_ids=new_connected_points)


def remove_point_from_connected_cards(origin_identifier, point_to_remove, points_type):
    for widget in g.grid_controller.widgets.values():
        if widget.identifier != origin_identifier:
            widget.remove_connected_point(point_to_remove, points_type)


def get_data_from_widget_to_compute_masks(widget):
    widget_data = widget.get_data_to_send()
    return {
            "crop": [
                {
                    "x": widget_data['scaledBbox'][0][0],
                    "y": widget_data['scaledBbox'][0][1]
                },
                {
                    "x": widget_data['scaledBbox'][1][0],
                    "y": widget_data['scaledBbox'][1][1]
                }
            ],
            "positive": [
                {
                    "x": positive_point['position'][0][0],
                    "y": positive_point['position'][0][1]
                } for positive_point in widget_data['positivePoints']
            ],
            "negative": [
                {
                    "x": negative_points['position'][0][0],
                    "y": negative_points['position'][0][1]
                } for negative_points in widget_data['negativePoints']
            ],
            "image_hash": f"{widget_data['imageHash']}"
        }


def get_data_to_process():
    data_to_send = {}
    for index, widget in enumerate(g.grid_controller.widgets.values()):
        if widget.needs_an_update:
            widget.needs_an_update = False
            data_to_send[index] = get_data_from_widget_to_compute_masks(widget)
    return data_to_send
