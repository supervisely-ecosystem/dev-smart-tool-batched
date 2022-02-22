from queue import Queue

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
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=identifier))
    project_datasets = g.api.dataset.get_list(project_id=identifier)

    for current_dataset in project_datasets:
        images_in_dataset = g.api.image.get_list(dataset_id=current_dataset.id)
        annotations_in_dataset = local_functions.get_annotations_for_dataset(dataset_id=current_dataset.id,
                                                                             images=images_in_dataset)

        for current_image, current_annotation in zip(images_in_dataset, annotations_in_dataset):
            local_functions.put_crops_to_queue(selected_image=current_image,
                                               img_annotation_json=current_annotation,
                                               project_meta=project_meta)

    state['currentStep'] = 2
    state['inputProject']['loading'] = False
    async_to_sync(state.synchronize_changes)()


def select_output_project(identifier: str,
                          request: Request,
                          state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):

    if state['outputProject']['mode'] == 'new':
        local_functions.create_new_project_by_name(state)

    state['currentStep'] = 3
    async_to_sync(state.synchronize_changes)()


def select_output_class(identifier: str,
                        request: Request,
                        state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):

    g.output_class_object = local_functions.get_object_class_by_name(state)

    state['currentStep'] = 4

    grid_controller_handlers.windows_count_changed(request=request, state=state)
    async_to_sync(state.synchronize_changes)()
