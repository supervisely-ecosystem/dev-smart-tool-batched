import copy
from queue import Queue

from loguru import logger

from asgiref.sync import async_to_sync
from fastapi import Request, Depends

import src.sly_functions as f
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson, StateJson

import src.settings_card.functions as local_functions

import src.grid_controller.handlers as grid_controller_handlers

import src.sly_functions as global_functions


def connect_to_model(identifier: str,
                     request: Request,
                     state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):

    state['currentStep'] = 1
    async_to_sync(state.synchronize_changes)()


def get_output_project_id():
    for project in g.api.project.get_list(workspace_id=DataJson()['workspaceId']):
        if project.name == f'{g.api.project.get_info_by_id(g.input_project_id).name}_BST':
            return project.id


def select_output_project(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.imagehash2imageinfo_by_datasets = {}  # reset output images cache
    g.grid_controller.clean_all(state=state, data=DataJson(), images_queue=g.selected_queue)

    if state['outputProject']['mode'] == 'new':
        local_functions.create_new_project_by_name(state)
    else:
        state['outputProject']['id'] = get_output_project_id()
        local_functions.cache_existing_images(state)
        local_functions.remove_processed_geometries(state)

    g.output_project_id = state['outputProject']['id']
    select_output_class(state=state)  # selecting first class from table

    state['outputProject']['loading'] = False
    state['outputProject']['dialogVisible'] = False
    async_to_sync(state.synchronize_changes)()


def select_output_class(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    local_functions.update_output_class(state)

    g.grid_controller.clean_all(state=state, data=DataJson(), images_queue=g.selected_queue)
    g.output_class_object = local_functions.get_object_class_by_name(state)

    local_functions.update_selected_queue(state)
    state['queueIsEmpty'] = g.selected_queue.empty()

    grid_controller_handlers.windows_count_changed(state=state)
    async_to_sync(state.synchronize_changes)()
