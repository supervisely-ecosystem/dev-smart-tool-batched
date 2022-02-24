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


def connect_to_model(identifier: str,
                     request: Request,
                     state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    print('model connected')
    state['currentStep'] = 1
    async_to_sync(state.synchronize_changes)()


def select_input_project(identifier: str,
                         request: Request,
                         state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.grid_controller.clean_all(state=state, data=DataJson())
    local_functions.refill_queues_by_input_project_data(project_id=identifier)

    g.processing_queue_backup = copy.deepcopy(g.bboxes_to_process.queue)

    state['currentStep'] = 2
    state['inputProject']['loading'] = False
    async_to_sync(state.synchronize_changes)()


def select_output_project(identifier: str,
                          request: Request,
                          state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.imagehash2imageinfo_by_datasets = {}  # reset output images cache

    if state['outputProject']['mode'] == 'new':
        local_functions.create_new_project_by_name(state)
    else:
        local_functions.cache_existing_images(state)

    state['currentStep'] = 3
    state['outputProject']['loading'] = False
    async_to_sync(state.synchronize_changes)()


def select_output_class(identifier: str,
                        request: Request,
                        state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    g.grid_controller.clean_all(state=state, data=DataJson())
    g.bboxes_to_process.queue = copy.deepcopy(g.processing_queue_backup)

    g.output_class_object = local_functions.get_object_class_by_name(state)

    state['currentStep'] = 4

    grid_controller_handlers.windows_count_changed(request=request, state=state)
    async_to_sync(state.synchronize_changes)()
