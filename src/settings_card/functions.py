import copy
import functools
from queue import Queue

import numpy as np
from loguru import logger

from supervisely.app.fastapi import run_sync

import supervisely

import src.sly_globals as g
from supervisely.app import DataJson

import src.select_class as select_class

import src.sly_functions as global_functions
import src.dialog_window as dialog_window


def get_bboxes_from_annotation(image_annotations):
    bboxes = []
    for label in image_annotations.labels:
        if label.geometry.geometry_name() == 'rectangle':
            bbox = label.geometry.to_bbox()
            bboxes.append({
                'label': label.obj_class.name,
                'bbox': bbox,
                'sly_id': label.geometry.sly_id
            })

    return bboxes


def get_data_to_render(image_info, bboxes, current_dataset):
    data_to_render = []

    for bbox_item in bboxes:
        label = bbox_item['label']
        sly_id = bbox_item.get('sly_id')
        bbox = bbox_item['bbox']

        data_to_render.append({
            'label': label,
            'imageLink': f'{g.api.image.url(team_id=DataJson()["teamId"], workspace_id=DataJson()["workspaceId"], project_id=current_dataset.project_id, dataset_id=current_dataset.id, image_id=image_info.id)}',
            'imageUrl': f'{image_info.full_storage_url}',
            'imageHash': f'{image_info.hash}',
            'imageSize': [image_info.width, image_info.height],
            'datasetName': f'{current_dataset.name}',
            'datasetId': f'{current_dataset.id}',
            'originalBbox': [[bbox.left, bbox.top], [bbox.right, bbox.bottom]],
            'scaledBbox': [[bbox.left, bbox.top], [bbox.right, bbox.bottom]],
            'positivePoints': [],
            'negativePoints': [],
            'mask': None,
            'isActive': True,
            'slyId': sly_id,

            'boxArea': (bbox.right - bbox.left) * (bbox.bottom - bbox.top)
        })

    return data_to_render


def put_data_to_queues(data_to_render):
    for item in data_to_render:
        if item['label'] != 'image':
            g.classes2queues.setdefault(item['label'], Queue(maxsize=int(1e6))).put(item)
        else:
            g.images_queue.put(item)


def get_annotations_for_dataset(dataset_id, images):
    images_ids = [image_info.id for image_info in images]
    return g.api.annotation.download_batch(dataset_id=dataset_id, image_ids=images_ids)


def get_crops_for_queue(selected_image, img_annotation_json, current_dataset, project_meta):
    image_annotation = supervisely.Annotation.from_json(img_annotation_json.annotation, project_meta)

    bboxes = get_bboxes_from_annotation(image_annotation)
    data_to_render = get_data_to_render(selected_image, bboxes, current_dataset)
    return data_to_render


def create_new_project_by_name(state):
    project_name = f'{g.api.project.get_info_by_id(g.input_project_id).name}_BST'

    created_project = g.api.project.create(workspace_id=DataJson()['workspaceId'],
                                           name=project_name,
                                           change_name_if_conflict=True)

    state['outputProject']['id'] = created_project.id


def create_new_object_meta_by_name(output_class_name, geometry_type):
    objects = supervisely.ObjClassCollection(
        [supervisely.ObjClass(name=output_class_name, geometry_type=geometry_type,
                              color=list(np.random.choice(range(256), size=3)))])

    return supervisely.ProjectMeta(obj_classes=objects, project_type=supervisely.ProjectType.IMAGES)


def get_object_class_by_name(state, output_class_name, geometry_type=supervisely.Bitmap):
    output_project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=state['outputProject']['id']))
    obj_class = output_project_meta.obj_classes.get(output_class_name, None)

    while obj_class is None or obj_class.geometry_type is not geometry_type:
        if obj_class is not None and obj_class.geometry_type is not geometry_type:
            output_class_name += '_BST'

        updated_meta = output_project_meta.merge(create_new_object_meta_by_name(output_class_name, geometry_type))
        g.api.project.update_meta(id=state['outputProject']['id'], meta=updated_meta.to_json())

        output_project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=state['outputProject']['id']))
        obj_class = output_project_meta.obj_classes.get(output_class_name, None)

    return obj_class


def cache_existing_images(state):
    output_project_id = state['outputProject']['id']
    datasets_in_output_project = g.api.dataset.get_list(project_id=output_project_id)

    for current_dataset in datasets_in_output_project:
        images_info = g.api.image.get_list(dataset_id=current_dataset.id)

        g.imagehash2imageinfo_by_datasets[current_dataset.id] = {image_info.hash: image_info for image_info in
                                                                 images_info}

    return state


def get_images_for_queue(selected_image, current_dataset):
    bbox = {
        'bbox': supervisely.Rectangle(top=0, left=0, bottom=selected_image.height - 1, right=selected_image.width - 1),
        'label': 'image'
    }

    data_to_render = get_data_to_render(image_info=selected_image,
                                        bboxes=[bbox],
                                        current_dataset=current_dataset)

    return data_to_render


def update_additional_data(current_image, current_annotation):
    image_annotation = supervisely.Annotation.from_json(data=current_annotation.annotation,
                                                        project_meta=g.input_project_meta)

    for label in image_annotation.labels:
        if label.geometry.geometry_name() == 'rectangle':
            g.labelid2labelann[label.geometry.sly_id] = label

    g.imagehash2imageann[current_image.hash] = image_annotation


def refill_queues_by_input_project_data(project_id):
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=project_id))
    g.input_project_meta = project_meta.clone()

    project_datasets = g.api.dataset.get_list(project_id=project_id)

    crops_data = []

    for current_dataset in dialog_window.datasets_progress(project_datasets, message='downloading datasets'):
        images_in_dataset = g.api.image.get_list(dataset_id=current_dataset.id)
        annotations_in_dataset = get_annotations_for_dataset(dataset_id=current_dataset.id,
                                                             images=images_in_dataset)

        for current_image, current_annotation in dialog_window.images_progress(
                zip(images_in_dataset, annotations_in_dataset), total=len(images_in_dataset),
                message='downloading images'):
            crops_data.extend(get_crops_for_queue(selected_image=current_image,
                                                  img_annotation_json=current_annotation,
                                                  current_dataset=current_dataset,
                                                  project_meta=project_meta))

            crops_data.extend(get_images_for_queue(selected_image=current_image,
                                                   current_dataset=current_dataset))

            update_additional_data(current_image, current_annotation)

    g.crops_data = crops_data


def select_input_project(identifier: str, state):
    g.grid_controller.clean_all(state=state, data=DataJson())
    refill_queues_by_input_project_data(project_id=identifier)


def update_output_class(state):
    try:
        selected_row = select_class.classes_table.get_selected_row(state)
    except IndexError:
        selected_row = None

    if state['queueMode'] == 'objects' and selected_row is not None:
        g.output_class_name = selected_row[0]
    else:
        state['queueMode'] = 'images'
        g.output_class_name = 'image'


def update_selected_queue(state):
    if state['queueMode'] == 'objects':
        g.selected_queue = g.classes2queues[g.output_class_name]
    else:
        g.selected_queue = g.images_queue


def remove_processed_geometries(state):
    custom_data = global_functions.get_project_custom_data(state['outputProject']['id']).get('_batched_smart_tool', {})
    processed_geometries_ids = custom_data.get('processed_geometries', [])

    for label, queue in g.classes2queues.items():
        updated_queue = Queue(maxsize=int(1e6))
        for item in queue.queue:
            if item['slyId'] not in processed_geometries_ids:
                updated_queue.put(item)

        g.classes2queues[label] = updated_queue

    select_class.update_classes_table()
    run_sync(DataJson().synchronize_changes())


def get_output_project_id():
    for project in g.api.project.get_list(workspace_id=DataJson()['workspaceId']):
        if project.name == f'{g.api.project.get_info_by_id(g.input_project_id).name}_BST':
            return project.id


def copy_meta_from_input_to_output(output_project_id):
    meta = supervisely.ProjectMeta.from_json(data=g.api.project.get_meta(output_project_id))
    meta = meta.merge(other=g.input_project_meta)
    g.api.project.update_meta(output_project_id, meta.to_json())


def add_tag_to_project_meta(project_id, tag_name):
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(project_id))
    tag_meta = supervisely.TagMeta(name=tag_name, value_type=supervisely.TagValueType.ANY_STRING)
    project_meta = project_meta.clone(tag_metas=project_meta.tag_metas.add(tag_meta))
    g.api.project.update_meta(project_id, project_meta.to_json())

    logger.info(f'new tag added to project meta: {project_id=}, {tag_name=}')

    return tag_meta


def get_tag_from_project_meta(project_id, tag_name):
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(project_id))
    tag_meta = project_meta.tag_metas.get(tag_name, None)
    if tag_meta is None:
        tag_meta = add_tag_to_project_meta(project_id, tag_name)
    return tag_meta
