import supervisely

import src.sly_globals as g


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


def get_annotations_for_dataset(dataset_id, images):
    images_ids = [image_info.id for image_info in images]
    return g.api.annotation.download_batch(dataset_id=dataset_id, image_ids=images_ids)


def put_crops_to_queue(selected_image, img_annotation_json, project_meta):
    image_annotation = supervisely.Annotation.from_json(img_annotation_json.annotation, project_meta)

    bboxes = get_bboxes_from_annotation(image_annotation)
    data_to_render = get_data_to_render(selected_image, bboxes)
    put_data_to_queue(data_to_render)
