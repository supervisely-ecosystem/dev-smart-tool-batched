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
    print('model connected')
    state['currentStep'] = 1
    async_to_sync(state.synchronize_changes)()


def select_output_project(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.imagehash2imageinfo_by_datasets = {}  # reset output images cache

    # if state['outputProject']['mode'] == 'new':
    local_functions.create_new_project_by_name(state)
    # else:
    #     local_functions.cache_existing_images(state)

    state['currentStep'] = 3
    state['outputProject']['loading'] = False
    async_to_sync(state.synchronize_changes)()


def select_output_class(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    local_functions.update_output_class(state)

    g.grid_controller.clean_all(state=state, data=DataJson(), images_queue=g.selected_queue)
    g.output_class_object = local_functions.get_object_class_by_name(state)

    local_functions.update_selected_queue(state)
    state['queueIsEmpty'] = g.selected_queue.empty()

    grid_controller_handlers.windows_count_changed(state=state)
    async_to_sync(state.synchronize_changes)()
