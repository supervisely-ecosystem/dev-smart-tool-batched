import os
import uuid

import jinja2
from asgiref.sync import async_to_sync
from starlette.templating import Jinja2Templates

import sly_globals as g
import supervisely
from sly_tqdm import sly_tqdm


async def get_widget_arguments_from_request(request):
    content = await request.json()
    payload = content.get('payload', {})
    # identifier = payload.get('identifier')
    return payload


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


def get_mask_from_processing_server(current_card, processing_session_id):
    context = {
        "crop": [
            {
                "x": current_card['bbox'][0][0],
                "y": current_card['bbox'][0][1]
            },
            {
                "x": current_card['bbox'][1][0],
                "y": current_card['bbox'][1][1]
            }
        ],
        "positive": [
            {
                "x": positive_point['position'][0][0],
                "y": positive_point['position'][0][1]
            } for positive_point in current_card['positivePoints']
        ],
        "negative": [
            {
                "x": negative_points['position'][0][0],
                "y": negative_points['position'][0][1]
            } for negative_points in current_card['negativePoints']
        ],
        "image_hash": f"{current_card['imageHash']}"
    }
    response = g.api.task.send_request(processing_session_id, "smart_segmentation", data={},
                                       context=context)

    if response.get('bitmap') is not None:
        return {
            'data': response.get('bitmap'),
            'origin': [response['origin']['x'], response['origin']['y']],
            'color': '#77e377'
        }
    else:
        return None


def get_box_size(current_card):
    box_width = current_card['bbox'][1][0] - current_card['bbox'][0][0]
    box_height = current_card['bbox'][1][1] - current_card['bbox'][0][1]

    return box_width, box_height


def add_rel_points_to_all_active_cards(state, rel_coordinates, origin_identifier):
    updated_cards = {}

    for card_id, current_card in state['widgets'].items():
        bbox = current_card.get('bbox', [])
        if len(bbox) > 1 and card_id != origin_identifier and current_card.get('isActive', False):
            width, height = get_box_size(current_card)
            x_real = int(rel_coordinates['x'] * width + current_card['bbox'][0][0])
            y_real = int(rel_coordinates['y'] * height + current_card['bbox'][0][1])

            point_id = f'{uuid.uuid4()}'
            g.relative_points.add(point_id)

            current_card[rel_coordinates['refers']].append({'position': [[x_real, y_real]],
                                                            'id': point_id})

            state['widgets'][card_id] = current_card

            updated_cards[card_id] = current_card

    return updated_cards


def get_new_relative_point_coordinates(current_card):
    box_width, box_height = get_box_size(current_card)

    for refers_flag in ['positivePoints', 'negativePoints']:
        for positive_point in current_card[refers_flag]:
            if positive_point['id'] not in g.relative_points:
                g.relative_points.add(positive_point['id'])

                return {
                    'x': (positive_point['position'][0][0] - current_card['bbox'][0][0]) / box_width,
                    'y': (positive_point['position'][0][1] - current_card['bbox'][0][1]) / box_height,
                    'refers': refers_flag
                }


def get_smart_segmentation_tool_cards(state):
    smart_segmentation_tool_cards = {}
    for card_id, current_card in state['widgets'].items():
        if len(current_card.get('bbox', [])) > 1:
            smart_segmentation_tool_cards[card_id] = current_card
    return smart_segmentation_tool_cards


def update_masks(state):
    actual_cards = get_smart_segmentation_tool_cards(state)
    for card_id, current_card in sly_tqdm(actual_cards.items(), identifier='progress_1', message='updating masks'):
        mask = get_mask_from_processing_server(current_card=current_card,
                                               processing_session_id=state['processingServerSessionId'])

        if mask is not None:
            state['widgets'][f'{card_id}']['mask'] = mask
            async_to_sync(state.synchronize_changes)()


def get_label_by_card(current_card):
    if current_card.get('mask') is not None:
        mask_np = supervisely.Bitmap.base64_2_data(current_card['mask']['data'])
        geometry = supervisely.Bitmap(data=mask_np,
                                      origin=supervisely.PointLocation(row=current_card['mask']['origin'][1],
                                                                       col=current_card['mask']['origin'][0]))

        label = supervisely.Label(geometry=geometry,
                                  obj_class=supervisely.ObjClass("batched_smart_tool", supervisely.Bitmap))

        return label


def upload_images_to_dataset(dataset_id, smart_segmentation_tool_cards):
    hash2annotation = {}
    hash2labels = {}

    for card_id, current_card in smart_segmentation_tool_cards.items():
        label = get_label_by_card(current_card)
        if label is not None:
            hash2labels.setdefault(current_card['imageHash'], []).append(label)

    for image_hash, labels in sly_tqdm(hash2labels.items(), identifier='progress_1', message='uploading to project'):
        if len(labels) > 0:
            image_info = g.api.image.upload_hash(dataset_id=dataset_id, name=f'{image_hash[:5]}.png', hash=image_hash)

            annotation = supervisely.Annotation(img_size=(image_info.height, image_info.width),
                                                labels=labels)
            g.api.annotation.upload_ann(image_info.id, annotation)
            # print()

    return hash2annotation
