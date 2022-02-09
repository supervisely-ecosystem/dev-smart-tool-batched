import os

import jinja2
from starlette.templating import Jinja2Templates

import sly_globals as g


async def get_widget_identifier_from_request(request):
    content = await request.json()
    payload = content.get('payload', {})
    identifier = payload.get('identifier')
    return identifier


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
