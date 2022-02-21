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
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import create, Jinja2Templates


from src.grid_controller import GridController


app = FastAPI()

sly_app = create()

app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory="../static"), name="static")

api = supervisely.Api.from_env()

app_dir = str(Path(sys.argv[0]).parents[1])
print(f"App root directory: {app_dir}")
local_project_dir = os.path.join(app_dir, 'local_project')


class EnvVariables:
    TEAM_ID = os.environ['context.teamId']
    WORKSPACE_ID = os.environ['context.workspaceId']


StateJson(
    {
        'currentState': 0,  # 0 — setting page, 1 — batched smart tool page
        'widgets': {},
    }
)

DataJson(
    {
        'teamId': EnvVariables.TEAM_ID,
        'workspaceId': EnvVariables.WORKSPACE_ID,

        'widgets': {},
    }
)

templates_env = Jinja2Templates(directory="../templates")

bboxes_to_process = Queue(maxsize=512)
grid_controller = GridController(SmartTool)

imagehash2imageinfo = {}

selected_object_class = None


@app.get('/favicon.ico')
def favicon():
    return FileResponse('../static/favicon.png')
