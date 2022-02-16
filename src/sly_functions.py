import os
import uuid

import jinja2
from asgiref.sync import async_to_sync
from starlette.templating import Jinja2Templates

import sly_globals as g
import supervisely
from sly_tqdm import sly_tqdm






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
