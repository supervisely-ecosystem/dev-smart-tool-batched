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
import src.select_class.local_widgets as select_class_widgets


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
    selected_row = select_class_widgets.classes_table.get_selected_row(state)

    if selected_row is not None:
        g.output_class_name = selected_row[0]
    else:
        g.output_class_name = list(g.classes2queues.keys())[0]

    g.grid_controller.clean_all(state=state, data=DataJson(), images_queue=g.selected_queue)
    g.output_class_object = local_functions.get_object_class_by_name(state)

    g.selected_queue = g.classes2queues[g.output_class_name]

    state['queueIsEmpty'] = len(g.selected_queue.queue) == 0
    state['selectClassVisible'] = False
    state['outputClassName'] = g.output_class_name
    state['updatingClass'] = False

    grid_controller_handlers.windows_count_changed(state=state)
    async_to_sync(state.synchronize_changes)()


