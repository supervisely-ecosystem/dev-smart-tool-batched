import uvicorn  # 🪐 server tools
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
    print('render_tamplate')
    return g.templates_env.TemplateResponse('index.html', {'request': request,
                                                           'smart_tool': smart_tool})


@g.app.post("/update_annotation")
async def update_annotation(request: Request, state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    identifier = await f.get_widget_identifier_from_request(request)
    print(identifier)
    if identifier is not None:
        changed_card = state['widgets'][f'{identifier}']


if __name__ == "__main__":
    uvicorn.run(g.app, host="0.0.0.0", port=8000)

