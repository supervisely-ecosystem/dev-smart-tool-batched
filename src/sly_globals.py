import os
import sys
from loguru import logger
from pathlib import Path

from asgiref.sync import async_to_sync
from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from queue import Queue

import supervisely
from sly_tqdm import sly_tqdm
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


DataJson(
    {
        'teamId': os.environ['context.teamId'],
        'workspaceId': os.environ['context.workspaceId'],

        'widgets': {},
    }
)

templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))


bboxes_to_process = Queue(maxsize=int(1e6))
processing_queue_backup = None

grid_controller = GridController(SmartTool)

imagehash2imageinfo_by_datasets = {}

output_class_object = None


@app.get('/favicon.ico')
def favicon():
    return FileResponse(os.path.join(app_root_directory, 'static', 'favicon.png'))
