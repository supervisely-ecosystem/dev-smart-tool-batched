import uvicorn  # 🪐 server tools
from asgiref.sync import async_to_sync
from pydantic import BaseModel
from starlette.responses import FileResponse
from fastapi import Request, WebSocket, Depends

import os  # 🔧 system tools
import time

import supervisely  # 🤖 general
from supervisely.app import StateJson, DataJson

import sly_globals as g
import sly_functions as f

from smart_tool import smart_tool  # 🤖 widgets


@g.app.get("/")
async def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request,
                                                           'smart_tool': smart_tool})


@g.app.post("/get_image_from_dataset")
async def get_image_from_dataset(request: Request,
                                 state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=9099))
    images_in_dataset = g.api.image.get_list(dataset_id=43859)

    selected_image = images_in_dataset[0]

    image_ann_json = g.api.annotation.download(selected_image.id)

    image_annotation = supervisely.Annotation.from_json(image_ann_json.annotation, project_meta)

    bboxes = f.get_bboxes_from_annotation(image_annotation)
    data_to_render = f.get_data_to_render(selected_image, bboxes)

    for identifier in range(len(data_to_render)):
        # for identifier in range(len(data_to_render)):
        smart_tool.update_data(identifier=f'{identifier}', data_to_upload=data_to_render[identifier], state=state)

    await state.synchronize_changes()

    # print(images_in_dataset)


@g.app.post("/update_annotation")
async def update_annotation(request: Request,
                            state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    identifier = await f.get_widget_identifier_from_request(request)

    if identifier is not None:
        changed_card = state['widgets'][f'{identifier}']

        context = {
            "crop": [
                {
                    "x": changed_card['bbox'][0][0],
                    "y": changed_card['bbox'][0][1]
                },
                {
                    "x": changed_card['bbox'][1][0],
                    "y": changed_card['bbox'][1][1]
                }
            ],
            "positive": [
                {
                    "x": positive_point['position'][0][0],
                    "y": positive_point['position'][0][1]
                } for positive_point in changed_card['positivePoints']
            ],
            "negative": [
                {
                    "x": negative_points['position'][0][0],
                    "y": negative_points['position'][0][1]
                } for negative_points in changed_card['negativePoints']
            ],
            "image_hash": f"{changed_card['imageHash']}"
        }
        response = g.api.task.send_request(state['processingServerSessionId'], "smart_segmentation", data={},
                                           context=context)

        state['widgets'][f'{identifier}']['mask'] = {
            'data': response.get('bitmap'),
            'origin': [response['origin']['x'], response['origin']['y']],
            'color': '#77e377'
        }

        await state.synchronize_changes()
        print()


if __name__ == "__main__":
    uvicorn.run(g.app, host="0.0.0.0", port=8000)
