from asgiref.sync import async_to_sync
from fastapi import Request, WebSocket, Depends

import supervisely
from smart_tool import SmartTool

import sly_globals as g
from supervisely.app import DataJson


# ------------------
# HANDLERS CODE PART
# ------------------


def points_updated(identifier: str,
                   request: Request,
                   state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    widget: SmartTool = g.grid_controller.get_widget_by_id(widget_id=identifier)

    updated_points = {}
    removed_points = {}
    for points_type in ['positive', 'negative']:
        updated_points[points_type] = widget.get_updated_points(state=state, data=None, points_type=points_type)
        removed_points[points_type] = widget.get_removed_points(state=state, data=None, points_type=points_type)

    # update all local objects by state
    g.grid_controller.update_local_fields(state=state, data=DataJson())

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
        widget.is_active = is_active

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


def clean_points(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    for widget in g.grid_controller.widgets.values():
        widget.clean_points()

    g.grid_controller.update_remote_fields(state=state, data=DataJson())


# ------------------
# CLASSIC CODE PART
# ------------------


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

