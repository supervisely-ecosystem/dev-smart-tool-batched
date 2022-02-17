from asgiref.sync import async_to_sync
from fastapi import Request, WebSocket, Depends

import supervisely
from smart_tool import SmartTool

import sly_functions as f
import sly_globals as g

from supervisely.app import DataJson


# ------------------
# HANDLERS CODE PART
# ------------------


def points_updated(identifier: str,
                   request: Request,
                   state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    widget: SmartTool = g.grid_controller.get_widget_by_id(widget_id=identifier)
    widget.needs_an_update = True

    updated_points = {}
    removed_points = {}
    for points_type in ['positive', 'negative']:
        updated_points[points_type] = widget.get_updated_points(state=state, data=None, points_type=points_type)
        removed_points[points_type] = widget.get_removed_points(state=state, data=None, points_type=points_type)

    # update all local objects by state
    g.grid_controller.update_local_fields(state=state, data=DataJson())

    if widget.is_active:
        # remove connected points
        for points_type in ['positive', 'negative']:
            removed_points_by_type = removed_points[points_type]
            for removed_point in removed_points_by_type:
                remove_point_from_connected_cards(origin_identifier=identifier, point_to_remove=removed_point,
                                                  points_type=points_type)

        # add new point to active cards
        for points_type in ['positive', 'negative']:
            updated_points_by_type = updated_points[points_type]
            for updated_point in updated_points_by_type:
                updated_point['relative'] = widget.get_relative_coordinates(updated_point)
                add_point_to_active_cards(origin_identifier=identifier, updated_point=updated_point,
                                          points_type=points_type)

    # update all remote state by local objects
    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def change_all_buttons(is_active: bool,
                       request: Request,
                       state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    for widget in g.grid_controller.widgets.values():
        if len(widget.bbox) > 0:
            widget.is_active = is_active

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def clean_points(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    for widget in g.grid_controller.widgets.values():
        widget.clean_points()

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def update_masks(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    data_to_process = get_data_to_process()
    response = g.api.task.send_request(state['processingServerSessionId'], "smart_segmentation_batched", data={},
                                       context={'data_to_process': data_to_process}, timeout=60)
    update_local_masks(response)

    state['updatingMasks'] = False
    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def next_batch(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['queueIsEmpty'] = g.bboxes_to_process.empty()

    # 1 - load data from widgets

    g.grid_controller.update_local_fields(state=state, data=DataJson())
    widgets_data = []
    for widget in g.grid_controller.widgets.values():
        widgets_data.append(widget.get_data_to_send())

    # 2 - upload data to project
    f.upload_images_to_dataset(dataset_id=g.output_dataset_id, data_to_upload=widgets_data)

    # 3 - load new data to widgets
    g.grid_controller.clean_all(state=state, data=DataJson())
    g.grid_controller.change_count(actual_count=state['windowsCount'], app=g.app, state=state, data=DataJson())
    #
    # for widget in g.grid_controller.widgets.values():
    #     if not g.bboxes_to_process.empty():
    #         new_data = g.bboxes_to_process.get()
    #         widget.update_fields_by_data(new_data)

    state['updatingMasks'] = False

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


# ------------------
# CLASSIC CODE PART
# ------------------


def update_local_masks(response):
    for index, widget in enumerate(g.grid_controller.widgets.values()):
        data = response.get(f'{index}')
        if data is not None:
            widget.mask = {
                'data': data.get('bitmap'),
                'origin': [data['origin']['x'], data['origin']['y']],
                'color': '#77e377'
            }


def add_point_to_active_cards(origin_identifier, updated_point, points_type):
    new_connected_points = set()

    for widget in g.grid_controller.widgets.values():
        if widget.is_active and widget.identifier != origin_identifier:
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


def get_data_to_process():
    data_to_send = {}
    for index, widget in enumerate(g.grid_controller.widgets.values()):
        if widget.needs_an_update:
            widget.needs_an_update = False

            widget_data = widget.get_data_to_send()
            data_to_send[index] = \
                {
                    "crop": [
                        {
                            "x": widget_data['bbox'][0][0],
                            "y": widget_data['bbox'][0][1]
                        },
                        {
                            "x": widget_data['bbox'][1][0],
                            "y": widget_data['bbox'][1][1]
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

    return data_to_send
