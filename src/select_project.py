import os
import shutil
from queue import Queue

from asgiref.sync import async_to_sync
from fastapi import Request, Depends
import supervisely

import sly_globals as g
import sly_functions as f
from sly_tqdm import sly_tqdm


# HANDLERS PART
from supervisely.app import DataJson


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
            image_to_crops(selected_image=current_image, project_meta=project_meta)

    g.output_project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=9100))
    g.output_dataset_id = f.get_remote_dataset_id()

    state['currentState'] = 1
    state['selectProjectLoading'] = False

    state['windowsCount'] = 0

    async_to_sync(state.synchronize_changes)()

# ------------------
# CLASSIC CODE PART
# ------------------


def get_bboxes_from_annotation(image_annotations):
    bboxes = []
    for label in image_annotations.labels:
        if label.geometry.geometry_name() == 'rectangle':
            bbox = label.geometry.to_bbox()
            bboxes.append(bbox)

    return bboxes


def get_data_to_render(image_info, bboxes):
    data_to_render = []

    for bbox in bboxes:
        data_to_render.append({
            'imageUrl': f'{image_info.full_storage_url}',
            'imageHash': f'{image_info.hash}',
            'bbox': [[bbox.left, bbox.top], [bbox.right, bbox.bottom]],
            'positivePoints': [],
            'negativePoints': [],
            'mask': None,
            'isActive': True
        })

    return data_to_render


def put_data_to_queue(data_to_render):
    for current_item in data_to_render:
        g.bboxes_to_process.put(current_item)


def image_to_crops(selected_image, project_meta):
    image_ann_json = g.api.annotation.download(selected_image.id)
    image_annotation = supervisely.Annotation.from_json(image_ann_json.annotation, project_meta)

    bboxes = get_bboxes_from_annotation(image_annotation)
    data_to_render = get_data_to_render(selected_image, bboxes)
    put_data_to_queue(data_to_render)

