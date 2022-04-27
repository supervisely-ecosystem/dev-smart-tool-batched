import asyncio
import functools
import os
import uuid

import jinja2
from starlette.templating import Jinja2Templates

import supervisely

import src.sly_globals as g

import src.select_class as select_class
from supervisely.app import DataJson


def get_supervisely_label_by_widget_data(widget_data):
    label = g.labelid2labelann.get(widget_data['slyId'], None)

    if widget_data.get('isBroken', False) and widget_data.get('originalBbox') is not None:
        if label is None:
            original_bbox = widget_data['originalBbox']
            geometry = supervisely.Rectangle(
                top=original_bbox[0][1], left=original_bbox[0][0],
                bottom=original_bbox[1][1], right=original_bbox[1][0]
            )

            label = supervisely.Label(geometry=geometry,
                                      obj_class=g.broken_image_object)

        label = label.add_tag(supervisely.Tag(meta=g.broken_tag_meta, value='not annotated'))

    elif widget_data.get('mask') is not None:
        mask_np = supervisely.Bitmap.base64_2_data(widget_data['mask']['data'])
        geometry = supervisely.Bitmap(data=mask_np,
                                      origin=supervisely.PointLocation(row=widget_data['mask']['origin'][1],
                                                                       col=widget_data['mask']['origin'][0]))

        if label is None:
            label = supervisely.Label(geometry=geometry,
                                      obj_class=g.output_class_object)

        else:
            label = label.clone(geometry=geometry,
                                obj_class=g.output_class_object)

    else:
        return None

    label = supervisely.Label(label.geometry, label.obj_class, label.tags,
                              label.description)  # check without recreation

    return label


def get_project_custom_data(project_id):
    project_info = g.api.project.get_info_by_id(project_id)
    if project_info.custom_data:
        return project_info.custom_data
    else:
        return {}


def append_processed_geometries(geometries_ids, project_id):
    project_custom_data = get_project_custom_data(project_id).get('_batched_smart_tool', {})

    project_custom_data.setdefault('processed_geometries', []).extend(geometries_ids)

    g.api.project.update_custom_data(project_id, {'_batched_smart_tool': project_custom_data})


def upload_images_to_dataset(dataset_id, data_to_upload):
    hash2annotation = {}
    hash2labels = {}
    hash2names = {}

    for widget_data in data_to_upload:
        label = get_supervisely_label_by_widget_data(widget_data)
        if label is not None:
            hash2labels.setdefault(widget_data['imageHash'], []).append(label)
            hash2names[widget_data['imageHash']] = widget_data['imageName']

    for image_hash, labels in hash2labels.items():
        if len(labels) > 0:
            imagehash2imageinfo = g.imagehash2imageinfo_by_datasets.get(dataset_id, {})
            image_info = imagehash2imageinfo.get(image_hash)

            if image_info is None:  # if image not founded in hashed images
                image_info = g.api.image.upload_hash(dataset_id=dataset_id, name=f'{hash2names[image_hash]}',
                                                     hash=image_hash)
                g.imagehash2imageinfo_by_datasets.setdefault(dataset_id, {})[image_hash] = image_info

                annotation = g.imagehash2imageann[image_info.hash].clone(labels=labels)

                g.api.annotation.upload_ann(image_info.id, annotation)
            else:
                g.api.annotation.append_labels(image_info.id, labels)

    append_processed_geometries(geometries_ids=[item['slyId'] for item in data_to_upload if item['slyId'] is not None],
                                project_id=g.output_project_id)

    return hash2annotation


@functools.lru_cache(maxsize=8)
def get_dataset_id_by_name(current_dataset_name, output_project_id):
    datasets_in_project = g.api.dataset.get_list(output_project_id)

    for current_dataset in datasets_in_project:
        if current_dataset.name == current_dataset_name:
            return current_dataset.id

    created_ds = g.api.dataset.create(project_id=output_project_id, name=current_dataset_name)
    return created_ds.id


def objects_left_number():
    obj_counter = 0
    for queue in g.classes2queues.values():
        obj_counter += len(queue.queue)
    return obj_counter


def update_queues_stats(state):
    state['selectClassVisible'] = False
    state['outputClassName'] = g.output_class_name
    state['updatingClass'] = False

    DataJson()['objectsLeftTotal'] = objects_left_number()
    DataJson()['objectsLeftQueue'] = len(g.selected_queue.queue)

    select_class.update_classes_table()

