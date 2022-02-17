import functools
import os
import uuid

import jinja2
from asgiref.sync import async_to_sync
from starlette.templating import Jinja2Templates

import sly_globals as g
import supervisely
from sly_tqdm import sly_tqdm


def get_remote_dataset_id():
    remote_dataset = g.api.dataset.create(project_id=9100, name="annotated", change_name_if_conflict=True)
    print(f'Dataset created {remote_dataset.name=}')
    return remote_dataset.id


def get_supervisely_label_by_widget_data(widget_data, current_class_name="batched_smart_tool"):
    if widget_data.get('mask') is not None:
        mask_np = supervisely.Bitmap.base64_2_data(widget_data['mask']['data'])
        geometry = supervisely.Bitmap(data=mask_np,
                                      origin=supervisely.PointLocation(row=widget_data['mask']['origin'][1],
                                                                       col=widget_data['mask']['origin'][0]))

        obj_class_id = g.output_project_meta.obj_classes.get(current_class_name)

        label = supervisely.Label(geometry=geometry,
                                  obj_class=obj_class_id)

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
            image_info = g.imagehash2imageinfo.get(image_hash)
            if image_info is None:
                image_info = g.api.image.upload_hash(dataset_id=dataset_id, name=f'{image_hash[:5]}.png', hash=image_hash)
                g.imagehash2imageinfo[image_hash] = image_info

                annotation = supervisely.Annotation(img_size=(image_info.height, image_info.width),
                                                    labels=labels)
                g.api.annotation.upload_ann(image_info.id, annotation)

            else:
                g.api.annotation.append_labels(image_info.id, labels)
            # print()

    return hash2annotation
