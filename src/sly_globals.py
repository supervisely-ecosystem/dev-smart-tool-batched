import os
import sys
from pathlib import Path

from asgiref.sync import async_to_sync
from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

import supervisely
from sly_tqdm import sly_tqdm
from supervisely.app import DataJson, LastStateJson
from supervisely.app.fastapi import create, Jinja2Templates

app_dir = str(Path(sys.argv[0]).parents[1])
print(f"App root directory: {app_dir}")

app = FastAPI()

sly_app = create()
app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory="../static"), name="static")

api = supervisely.Api.from_env()

LastStateJson(
    {
        'windowsCount': 0,
        'processingServerSessionId': 13303,
        'widgets': {},
        'finished': False
    }

)

DataJson(
    {
        'widgets': {},

    }
)

templates_env = Jinja2Templates(directory="../templates")
# templates_env.get_template('index.html').render(smart_tool=Smart, sly_tqdm=sly_tqdm)
#
#
async_to_sync(LastStateJson().synchronize_changes)()

relative_points = set()


@app.get('/favicon.ico')
def favicon():
    return FileResponse('../static/favicon.png')
