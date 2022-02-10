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
from sly_tqdm import sly_tqdm  # 🤖 widgets


@g.app.get("/")
async def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request,
                                                           'smart_tool': smart_tool,
                                                           'sly_tqdm': sly_tqdm})


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


@g.app.post("/update_masks")
def update_annotation(request: Request,
                            state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    f.update_masks(state)
    # state.synchronize_changes()


@g.app.post("/update_annotation")
async def update_annotation(request: Request,
                            state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    widget_arguments = await f.get_widget_arguments_from_request(request)

    identifier = widget_arguments.get('identifier')

    if identifier is not None:
        changed_card = state['widgets'][f'{identifier}']

        new_relative_point = f.get_new_relative_point_coordinates(changed_card)  # coordinates from 0 to 1
        if new_relative_point is not None:
            updated_cards = f.add_rel_points_to_all_active_cards(state, new_relative_point, origin_identifier=identifier)

        mask = f.get_mask_from_processing_server(current_card=changed_card,
                                                 processing_session_id=state['processingServerSessionId'])
        if mask is not None:
            state['widgets'][f'{identifier}']['mask'] = mask

        await state.synchronize_changes()


def create_empty_project():
    remote_dataset = g.api.dataset.create(project_id=9055, name="main", change_name_if_conflict=True)
    print(f'Dataset created {remote_dataset.name=}')



@g.app.post("/upload_to_project")
def upload_to_project(request: Request,
                            state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):

    create_empty_project()

    smart_segmentation_tool_cards = f.get_smart_segmentation_tool_cards(state)
    f.get_image_hash2annotation(smart_segmentation_tool_cards)






if __name__ == "__main__":
    uvicorn.run(g.app, host="0.0.0.0", port=8000)
