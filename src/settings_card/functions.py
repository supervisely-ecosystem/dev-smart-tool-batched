import functools


import numpy as np

import supervisely

import src.sly_globals as g
from supervisely.app import DataJson


def get_bboxes_from_annotation(image_annotations):
    bboxes = []
    for label in image_annotations.labels:
        if label.geometry.geometry_name() == 'rectangle':
            bbox = label.geometry.to_bbox()
            bboxes.append(bbox)

    return bboxes


def get_data_to_render(image_info, bboxes, current_dataset):
    data_to_render = []

    for bbox in bboxes:
        data_to_render.append({
            'imageUrl': f'{image_info.full_storage_url}',
            'imageHash': f'{image_info.hash}',
            'imageSize': [image_info.width, image_info.height],
            'datasetName': f'{current_dataset.name}',
            'originalBbox': [[bbox.left, bbox.top], [bbox.right, bbox.bottom]],
            'scaledBbox': [[bbox.left, bbox.top], [bbox.right, bbox.bottom]],
            'positivePoints': [],
            'negativePoints': [],
            'mask': None,
            'isActive': True
        })

    return data_to_render


def put_data_to_queue(data_to_render):
    for current_item in data_to_render:
        g.bboxes_to_process.put(current_item)


def get_annotations_for_dataset(dataset_id, images):
    images_ids = [image_info.id for image_info in images]
    return g.api.annotation.download_batch(dataset_id=dataset_id, image_ids=images_ids)


def put_crops_to_queue(selected_image, img_annotation_json, current_dataset, project_meta):
    image_annotation = supervisely.Annotation.from_json(img_annotation_json.annotation, project_meta)

    bboxes = get_bboxes_from_annotation(image_annotation)
    data_to_render = get_data_to_render(selected_image, bboxes, current_dataset)
    put_data_to_queue(data_to_render)


def create_new_project_by_name(state):
    created_project = g.api.project.create(workspace_id=DataJson()['workspaceId'],
                                           name=state['outputProject']['name'],
                                           change_name_if_conflict=True)

    state['outputProject']['id'] = created_project.id


def create_new_object_meta_by_name(output_class_name):
    objects = supervisely.ObjClassCollection(
        [supervisely.ObjClass(name=output_class_name, geometry_type=supervisely.Bitmap,
                              color=list(np.random.choice(range(256), size=3)))])

    return supervisely.ProjectMeta(obj_classes=objects, project_type=supervisely.ProjectType.IMAGES)


def get_object_class_by_name(state):
    output_class_name = state['outputClass']['name']

    output_project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=state['outputProject']['id']))
    obj_class = output_project_meta.obj_classes.get(output_class_name, None)

    while obj_class is None or obj_class.geometry_type is not supervisely.Bitmap:
        if obj_class is not None and obj_class.geometry_type is not supervisely.Bitmap:
            output_class_name += '_smart_tool'

        updated_meta = output_project_meta.merge(create_new_object_meta_by_name(output_class_name))
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


# @functools.lru_cache(maxsize=2)
def refill_queues_by_input_project_data(project_id):
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=project_id))
    project_datasets = g.api.dataset.get_list(project_id=project_id)

    for current_dataset in project_datasets:
        images_in_dataset = g.api.image.get_list(dataset_id=current_dataset.id)
        annotations_in_dataset = get_annotations_for_dataset(dataset_id=current_dataset.id,
                                                             images=images_in_dataset)

        for current_image, current_annotation in zip(images_in_dataset, annotations_in_dataset):
            put_crops_to_queue(selected_image=current_image,
                               img_annotation_json=current_annotation,
                               current_dataset=current_dataset,
                               project_meta=project_meta)
