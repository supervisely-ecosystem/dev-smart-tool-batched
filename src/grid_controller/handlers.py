from asgiref.sync import async_to_sync
from fastapi import Request, Depends

import supervisely
from supervisely.app import DataJson

import src.sly_globals as g

import src.sly_functions as global_functions


def windows_count_changed(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    windows_count = state['windowsCount']

    g.grid_controller.change_count(actual_count=windows_count, app=g.app, state=state, data=DataJson(),
                                   images_queue=g.selected_queue)

    global_functions.update_queues_stats(state)
    g.grid_controller.update_remote_fields(state=state, data=DataJson())
    DataJson().synchronize_changes()

