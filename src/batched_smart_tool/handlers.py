import copy
import uuid

from asgiref.sync import async_to_sync
from fastapi import Request, Depends

import supervisely
from smart_tool import SmartTool
from supervisely.app import DataJson

import src.sly_functions as f
import src.sly_globals as g

import src.select_class.functions as sc_functions

import src.batched_smart_tool.functions as local_functions
import src.sly_functions as global_functions

import src.dialog_window as dialog_window

from loguru import logger


def update_single_widget_realtime(widget_id, state):
    widget: SmartTool = g.grid_controller.get_widget_by_id(widget_id=widget_id)
    data_to_process = local_functions.get_data_from_widget_to_compute_masks(widget)

    response_data = g.api.task.send_request(int(state['processingServer']['sessionId']), "smart_segmentation",
                                            data={},
                                            context=data_to_process, timeout=60)

    if response_data.get('origin') is not None:
        local_functions.set_widget_mask_by_data(widget, response_data)
        widget.needs_an_update = False
    else:
        widget.mask = None

    widget.update_remote_fields(state=state, data=DataJson())


def new_masks_available_flag():
    for widget in g.grid_controller.widgets.values():
        if widget.needs_an_update:
            return True
    return False


def points_updated(identifier: str,
                   state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    widget: SmartTool = g.grid_controller.get_widget_by_id(widget_id=identifier)

    DataJson()['newMasksAvailable'] = True

    updated_points = {}
    removed_points = {}
    for points_type in ['positive', 'negative']:
        updated_points[points_type] = widget.get_updated_points(state=state, data=None, points_type=points_type)
        removed_points[points_type] = widget.get_removed_points(state=state, data=None, points_type=points_type)

    # update all local objects by state
    g.grid_controller.update_local_fields(state=state, data=DataJson())

    widget.needs_an_update = True
    if widget.is_active:
        # remove connected points
        for points_type in ['positive', 'negative']:
            removed_points_by_type = removed_points[points_type]
            for removed_point in removed_points_by_type:
                local_functions.remove_point_from_connected_cards(origin_identifier=identifier,
                                                                  point_to_remove=removed_point,
                                                                  points_type=points_type)

        # add new point to active cards
        for points_type in ['positive', 'negative']:
            updated_points_by_type = updated_points[points_type]
            for updated_point in updated_points_by_type:
                updated_point['relative'] = widget.get_relative_coordinates(updated_point)
                local_functions.add_point_to_active_cards(origin_identifier=identifier, updated_point=updated_point,
                                                          points_type=points_type)

    update_single_widget_realtime(widget_id=identifier, state=state)
    DataJson()['newMasksAvailable'] = new_masks_available_flag()

    # update all remote state by local objects
    g.grid_controller.update_remote_fields(state=state, data=DataJson())
    DataJson().synchronize_changes()


def change_all_buttons(is_active: bool,
                       request: Request,
                       state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    for widget in g.grid_controller.widgets.values():
        if len(widget.scaled_bbox) > 0:
            widget.is_active = is_active

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def clean_up(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.grid_controller.update_local_fields(state=state, data=DataJson())

    for widget in g.grid_controller.widgets.values():
        if widget.is_active and not widget.is_empty:
            widget.clean_up()
            widget.needs_an_update = False

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def assign_base_points(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.grid_controller.update_local_fields(state=state, data=DataJson())

    for widget in g.grid_controller.widgets.values():
        if widget.is_active and not widget.is_empty:
            widget.needs_an_update = True

            w = widget.scaled_bbox[1][0] - widget.scaled_bbox[0][0]
            h = widget.scaled_bbox[1][1] - widget.scaled_bbox[0][1]

            base_padding = 0.12

            x0, y0, x1, y1 = widget.scaled_bbox[0][0] + int(w * base_padding), \
                             widget.scaled_bbox[0][1] + int(h * base_padding), \
                             widget.scaled_bbox[1][0] - int(w * base_padding), \
                             widget.scaled_bbox[1][1] - int(h * base_padding)

            # new negative points on corners
            widget.negative_points.append({'position': [[x0, y0]], 'id': f'{uuid.uuid4()}'})
            widget.negative_points.append({'position': [[x0, y1]], 'id': f'{uuid.uuid4()}'})
            widget.negative_points.append({'position': [[x1, y0]], 'id': f'{uuid.uuid4()}'})
            widget.negative_points.append({'position': [[x1, y1]], 'id': f'{uuid.uuid4()}'})

            # new negative points on corners
            center_x, center_y = int((x0 + x1) / 2), int((y0 + y1) / 2)
            widget.positive_points.append({'position': [[center_x, center_y]], 'id': f'{uuid.uuid4()}'})

            # widget.needs_an_update = True
            # state['widgets'].setdefault(f'{widget.__class__.__name__}', {})[f'{widget.identifier}'] = \
            #     copy.deepcopy(widget.get_data_to_send())

            # widget.update_remote_fields(state=state, data=DataJson())  # update main card
            # for _ in range(4):
            #     widget.negative_points.pop()
            # widget.positive_points.pop()

            # points_updated(identifier=widget.identifier, state=state)  # update main card
            DataJson()['newMasksAvailable'] = new_masks_available_flag()

    DataJson().synchronize_changes()
    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def update_masks(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['dialogWindow']['mode'] = None

    data_to_process = local_functions.get_data_to_process()
    try:
        response = g.api.task.send_request(int(state['processingServer']['sessionId']), "smart_segmentation_batched",
                                           data={},
                                           context={'data_to_process': data_to_process}, timeout=60)
        local_functions.update_local_masks(response)
    except Exception as ex:
        dialog_window.notification_box.title = 'The model is not responding to requests.'
        dialog_window.notification_box.description = 'Please make sure the model is working and reconnect to it.'

        state['processingServer']['connected'] = False
        state['dialogWindow']['mode'] = 'modelConnection'
        logger.error(f'Exception while updating masks: {ex}')

    state['updatingMasks'] = False
    g.grid_controller.update_remote_fields(state=state, data=DataJson())

    DataJson()['newMasksAvailable'] = False
    DataJson().synchronize_changes()


def next_batch(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    logger.info(f'Items in queue left: {len(g.selected_queue.queue)}')
    state['queueIsEmpty'] = g.selected_queue.empty()

    # 1 - load data from widgets
    g.grid_controller.update_local_fields(state=state, data=DataJson())

    widgets_data_by_datasets = {}
    for widget in g.grid_controller.widgets.values():
        widget_data = widget.get_data_to_send()
        widgets_data_by_datasets.setdefault(widget.dataset_name, []).append(widget_data)

    # 2 - load new data to widgets
    g.grid_controller.clean_all(state=state, data=DataJson())
    g.grid_controller.change_count(actual_count=state['windowsCount'], app=g.app, state=state, data=DataJson(),
                                   images_queue=g.selected_queue)

    state['updatingMasks'] = False

    g.grid_controller.update_remote_fields(state=state, data=DataJson())

    # 3 - upload data to project
    for current_dataset_name, widget_data in widgets_data_by_datasets.items():
        if isinstance(current_dataset_name, str):
            ds_id = f.get_dataset_id_by_name(current_dataset_name, state['outputProject']['id'])
            f.upload_images_to_dataset(dataset_id=ds_id, data_to_upload=widget_data)

    state['batchInUpload'] = False

    # 4 - update stats in table
    sc_functions.update_classes_table()
    global_functions.update_queues_stats(state)

    state.synchronize_changes()
    DataJson().synchronize_changes()


def bboxes_padding_changed(request: Request,
                           state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    bboxes_padding = state['bboxesPadding']
    g.grid_controller.change_padding(actual_padding=bboxes_padding)
    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def bbox_updated(identifier: str,
                 state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    DataJson()['newMasksAvailable'] = True

    bboxes_padding = state['bboxesPadding'] / 100
    updated_widget: SmartTool = g.grid_controller.get_widget_by_id(widget_id=identifier)

    updated_widget.update_local_fields(state=state, data=DataJson())

    scaled_width, scaled_height = updated_widget.get_bbox_size(updated_widget.scaled_bbox)
    original_width, original_height = int(scaled_width / (1 + bboxes_padding)), int(
        scaled_height / (1 + bboxes_padding))

    div_width, div_height = (scaled_width - original_width) // 2, (scaled_height - original_height) // 2

    updated_widget.original_bbox[0][0] = updated_widget.scaled_bbox[0][0] + div_width
    updated_widget.original_bbox[0][1] = updated_widget.scaled_bbox[0][1] + div_height
    updated_widget.original_bbox[1][0] = updated_widget.scaled_bbox[1][0] - div_width
    updated_widget.original_bbox[1][1] = updated_widget.scaled_bbox[1][1] - div_height

    updated_widget.update_remote_fields(state=state, data=DataJson())
    DataJson().synchronize_changes()
