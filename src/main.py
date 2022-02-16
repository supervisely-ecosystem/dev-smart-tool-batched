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
import sly_widgets as w

from smart_tool import SmartTool  # 🤖 widgets
from sly_tqdm import sly_tqdm


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request,
                                                           'sly_tqdm': sly_tqdm,
                                                           'smart_tool': SmartTool})


@g.app.post("/windows-count-changed/")
def windows_count_changed(request: Request,
                          state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    windows_count = state['windowsCount']
    g.grid_controller.change_count(actual_count=windows_count, app=g.app, state=state, data=DataJson())






@g.app.post("/get_image_from_dataset")
async def get_image_from_dataset(request: Request,
                                 state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    project_meta = supervisely.ProjectMeta.from_json(g.api.project.get_meta(id=9131))
    images_in_dataset = g.api.image.get_list(dataset_id=43964)

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
            updated_cards = f.add_rel_points_to_all_active_cards(state, new_relative_point,
                                                                 origin_identifier=identifier)

        mask = f.get_mask_from_processing_server(current_card=changed_card,
                                                 processing_session_id=state['processingServerSessionId'])
        if mask is not None:
            state['widgets'][f'{identifier}']['mask'] = mask

        await state.synchronize_changes()


def get_remote_dataset_id():
    remote_dataset = g.api.dataset.create(project_id=9100, name="main", change_name_if_conflict=True)
    print(f'Dataset created {remote_dataset.name=}')
    return remote_dataset.id


@g.app.post("/upload_to_project")
def upload_to_project(request: Request,
                      state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    remote_dataset_id = get_remote_dataset_id()

    smart_segmentation_tool_cards = f.get_smart_segmentation_tool_cards(state)
    f.upload_images_to_dataset(dataset_id=remote_dataset_id,
                               smart_segmentation_tool_cards=smart_segmentation_tool_cards)

    state['finished'] = True
    async_to_sync(state.synchronize_changes)()


@g.app.post("/change_all_buttons")
async def change_all_buttons(request: Request,
                             state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    widget_arguments = await f.get_widget_arguments_from_request(request)
    mode = widget_arguments.get('mode')

    smart_segmentation_tool_cards = f.get_smart_segmentation_tool_cards(state)

    for card_id, current_card in smart_segmentation_tool_cards.items():
        current_card['isActive'] = True if mode == 'on' else False
        state['widgets'][card_id] = current_card

    await state.synchronize_changes()


if __name__ == "__main__":
    # g.app.add_api_route('/custom-post-req/{identifier}', test_method, methods=["POST"])


    uvicorn.run(g.app, host="0.0.0.0", port=8000)
