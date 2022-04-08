import asyncio
import os
import queue
import sys
from loguru import logger
from pathlib import Path


from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

import supervisely

from smart_tool import SmartTool
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import create, Jinja2Templates


from src.grid_controller import GridController

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
logger.info(f"App root directory: {app_root_directory}")
# sys.path.append(app_root_directory)
# local_project_dir = os.path.join(app_root_directory, 'local_project')
logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')


app = FastAPI()

sly_app = create()

app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory=os.path.join(app_root_directory, 'static')), name="static")

api = supervisely.Api.from_env()


StateJson()['widgets'] = {}


DataJson()['instanceAddress'] = os.environ['SERVER_ADDRESS']
DataJson()['teamId'] = os.environ['context.teamId']
DataJson()['workspaceId'] = os.environ['context.workspaceId']
DataJson()['widgets'] = {}

templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))

prediction_mode = 'batched'

# selected_queue = Queue(maxsize=int(1e6))
crops_data = None
bboxes_order = 'sizes'
selected_queue = None
classes2queues = {}
images_queue = queue.Queue(maxsize=int(1e6))

grid_controller = GridController(SmartTool)

imagehash2imageinfo_by_datasets = {}
imagehash2imageann = {}
labelid2labelann = {}

processed_geometries = []

output_class_name = None
output_class_object = None
broken_tag_meta = None

input_project_id = os.getenv('modal.state.slyProjectId')
input_project_meta = supervisely.ProjectMeta()
output_project_id = None

realtime_widget_update = 0


@app.get('/favicon.ico')
def favicon():
    return FileResponse(os.path.join(app_root_directory, 'static', 'favicon.png'))
