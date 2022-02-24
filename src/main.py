import uvicorn  # 🪐 server tools
from asgiref.sync import async_to_sync
from fastapi import Request, Depends
from starlette.middleware.cors import CORSMiddleware

import supervisely  # 🤖 general
from supervisely.app import DataJson, StateJson

import src.sly_functions as f
import src.sly_globals as g

from sly_tqdm import sly_tqdm
from smart_tool import SmartTool  # 🤖 widgets

import src.batched_smart_tool as batched_smart_tool
import src.settings_card as settings_card
import src.grid_controller as grid_controller

from src.sly_globals import app


@app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request,
                                                           'smart_tool': SmartTool})


# @TODO: add connect to model verification


app.add_api_route('/connect-to-model/{identifier}', settings_card.connect_to_model, methods=["POST"])
app.add_api_route('/select-input-project/{identifier}', settings_card.select_input_project, methods=["POST"])
app.add_api_route('/select-output-project/{identifier}', settings_card.select_output_project, methods=["POST"])
app.add_api_route('/select-output-class/{identifier}', settings_card.select_output_class, methods=["POST"])

app.add_api_route('/windows-count-changed/', grid_controller.windows_count_changed, methods=["POST"])

app.add_api_route('/change-all-buttons/{is_active}', batched_smart_tool.change_all_buttons, methods=["POST"])
app.add_api_route('/clean-points/', batched_smart_tool.clean_points, methods=["POST"])
app.add_api_route('/assign-base-points/', batched_smart_tool.assign_base_points, methods=["POST"])
app.add_api_route('/update-masks/', batched_smart_tool.update_masks, methods=["POST"])
app.add_api_route('/next-batch/', batched_smart_tool.next_batch, methods=["POST"])

app.add_api_route('/widgets/smarttool/negative-updated/{identifier}', batched_smart_tool.points_updated, methods=["POST"])
app.add_api_route('/widgets/smarttool/positive-updated/{identifier}', batched_smart_tool.points_updated, methods=["POST"])

uvicorn.run(app, host="127.0.0.1", port=8000)
