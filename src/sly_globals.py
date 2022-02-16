import os
import sys
from pathlib import Path

from asgiref.sync import async_to_sync
from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from queue import Queue

import supervisely
from sly_tqdm import sly_tqdm
from smart_tool import SmartTool
from supervisely.app import DataJson, LastStateJson
from supervisely.app.fastapi import create, Jinja2Templates

from src.sly_grid_controller import GridController

app_dir = str(Path(sys.argv[0]).parents[1])
print(f"App root directory: {app_dir}")
local_project_dir = os.path.join(app_dir, 'local_project')

app = FastAPI()

sly_app = create()
app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory="../static"), name="static")

api = supervisely.Api.from_env()

LastStateJson(
    {
        'currentState': 0,

        'windowsCount': 0,
        'toolSize': 20,

        'processingServerSessionId': 13303,
        'projectId': 9131,

        'widgets': {},

    }
)

DataJson(
    {
        'widgets': {},
        'teamId': '291',
        'dstProjectId': 0,
        'connectorOptions': {
            "sessionTags": [],
            "showLabel": False,
            "size": "small"
        }

    }
)

grid_controller = GridController(SmartTool)

templates_env = Jinja2Templates(directory="../templates")

bboxes_to_process = Queue(maxsize=999999)


@app.get('/favicon.ico')
def favicon():
    return FileResponse('../static/favicon.png')
