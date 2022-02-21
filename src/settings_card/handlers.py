
from queue import Queue

from asgiref.sync import async_to_sync
from fastapi import Request, Depends

import src.sly_functions as f
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson, StateJson

import src.settings_card.functions as local_functions


def download_project(identifier: str,
                     request: Request,
                     state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    # pbar = sly_tqdm(identifier='download_project', message='Downloading project')
    #
    # if os.path.isdir(g.local_project_dir):
    #     shutil.rmtree(g.local_project_dir)
    #
    # supervisely.download_project(api=g.api, project_id=identifier, dest_dir=g.local_project_dir,
    #                              progress_cb=pbar.update)
    #
    g.grid_controller.clean_all(state=state, data=DataJson())
    state['queueIsEmpty'] = False
    g.bboxes_to_process = Queue(maxsize=999999)

    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=identifier))
    project_datasets = g.api.dataset.get_list(project_id=identifier)

    for current_dataset in project_datasets:
        images_in_dataset = g.api.image.get_list(dataset_id=current_dataset.id)
        for current_image in images_in_dataset:
            local_functions.image_to_crops(selected_image=current_image, project_meta=project_meta)

    g.output_project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=9100))
    g.output_dataset_id = f.get_remote_dataset_id()

    g.selected_object_class = state['selectedClassName']
    # g.imagehash2imageinfo = {}

    state['currentState'] = 1
    state['selectProjectLoading'] = False

    state['windowsCount'] = 0

    async_to_sync(state.synchronize_changes)()
