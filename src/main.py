import uvicorn  # 🪐 server tools
from asgiref.sync import async_to_sync
from fastapi import Request, Depends

import supervisely  # 🤖 general
from src import select_project
from supervisely.app import DataJson

import sly_functions as f
import sly_globals as g
import smart_tool_handlers


from sly_tqdm import sly_tqdm
from smart_tool import SmartTool  # 🤖 widgets


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
    g.grid_controller.update_remote_fields(state=state, data=DataJson())

    # print(images_in_dataset)


@g.app.post("/update_masks")
def update_annotation(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    f.update_masks(state)
    # state.synchronize_changes()


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


if __name__ == "__main__":
    g.app.add_api_route('/download-project/{identifier}', select_project.download_project, methods=["POST"])

    g.app.add_api_route('/change-all-buttons/{is_active}', smart_tool_handlers.change_all_buttons, methods=["POST"])
    g.app.add_api_route('/clean-points/', smart_tool_handlers.clean_points, methods=["POST"])
    g.app.add_api_route('/update-masks/', smart_tool_handlers.update_masks, methods=["POST"])
    g.app.add_api_route('/next-batch/', smart_tool_handlers.next_batch, methods=["POST"])

    g.app.add_api_route('/widgets/smarttool/negative-updated/{identifier}', smart_tool_handlers.points_updated, methods=["POST"])
    g.app.add_api_route('/widgets/smarttool/positive-updated/{identifier}', smart_tool_handlers.points_updated, methods=["POST"])

    uvicorn.run(g.app, host="0.0.0.0", port=8000)
