import functools
import os
import uuid

import jinja2
from asgiref.sync import async_to_sync
from starlette.templating import Jinja2Templates

import supervisely
from sly_tqdm import sly_tqdm
import src.sly_globals as g


# import src.settings_card as settings_card


def get_supervisely_label_by_widget_data(widget_data, current_class_name="batched_smart_tool"):
    if widget_data.get('mask') is not None:
        mask_np = supervisely.Bitmap.base64_2_data(widget_data['mask']['data'])
        geometry = supervisely.Bitmap(data=mask_np,
                                      origin=supervisely.PointLocation(row=widget_data['mask']['origin'][1],
                                                                       col=widget_data['mask']['origin'][0]))

        # settings_card.get_object_class_by_name(state)

        label = supervisely.Label(geometry=geometry,
                                  obj_class=g.output_class_object)

        return label


def upload_images_to_dataset(dataset_id, data_to_upload):
    hash2annotation = {}
    hash2labels = {}

    for widget_data in data_to_upload:
        label = get_supervisely_label_by_widget_data(widget_data)
        if label is not None:
            hash2labels.setdefault(widget_data['imageHash'], []).append(label)

    # for image_hash, labels in sly_tqdm(hash2labels.items(), identifier='progress_1', message='uploading to project'):
    for image_hash, labels in hash2labels.items():
        if len(labels) > 0:
            imagehash2imageinfo = g.imagehash2imageinfo_by_datasets.get(dataset_id, {})
            image_info = imagehash2imageinfo.get(image_hash)

            if image_info is None:
                image_info = g.api.image.upload_hash(dataset_id=dataset_id, name=f'{image_hash[:5]}.png',
                                                     hash=image_hash)
                g.imagehash2imageinfo_by_datasets.setdefault(dataset_id, {})[image_hash] = image_info

                annotation = supervisely.Annotation(img_size=(image_info.height, image_info.width),
                                                    labels=labels)
                g.api.annotation.upload_ann(image_info.id, annotation)
            else:
                g.api.annotation.append_labels(image_info.id, labels)

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
