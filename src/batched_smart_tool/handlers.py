from fastapi import Request, Depends

import supervisely
from smart_tool import SmartTool
from supervisely.app import DataJson

import src.sly_functions as f
import src.sly_globals as g

import src.batched_smart_tool.functions as local_functions


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
    data_to_process = local_functions.get_data_to_process()
    response = g.api.task.send_request(int(state['processingServerSessionId']), "smart_segmentation_batched", data={},
                                       context={'data_to_process': data_to_process}, timeout=5)
    local_functions.update_local_masks(response)

    state['updatingMasks'] = False
    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def next_batch(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    state['queueIsEmpty'] = g.bboxes_to_process.empty()

    # 1 - load data from widgets
    g.grid_controller.update_local_fields(state=state, data=DataJson())

    widgets_data_by_datasets = {}
    for widget in g.grid_controller.widgets.values():
        widget_data = widget.get_data_to_send()
        widgets_data_by_datasets.setdefault(widget.dataset_name, []).append(widget_data)

    # 2 - upload data to project
    for current_dataset_name, widget_data in widgets_data_by_datasets.items():
        if isinstance(current_dataset_name, str):
            ds_id = f.get_dataset_id_by_name(current_dataset_name, state['outputProject']['id'])
            f.upload_images_to_dataset(dataset_id=ds_id, data_to_upload=widget_data)

    # 3 - load new data to widgets
    g.grid_controller.clean_all(state=state, data=DataJson())
    g.grid_controller.change_count(actual_count=state['windowsCount'], app=g.app, state=state, data=DataJson(),
                                   images_queue=g.bboxes_to_process)

    state['updatingMasks'] = False

    g.grid_controller.update_remote_fields(state=state, data=DataJson())
