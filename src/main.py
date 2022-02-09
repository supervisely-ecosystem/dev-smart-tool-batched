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

from sly_tqdm import sly_tqdm  # 🤖 widgets


@g.app.get("/")
async def read_index(request: Request):
    print('render_tamplate')
    return g.templates_env.TemplateResponse('index.html', {'request': request})

# class UpdatedAnnotation(BaseModel):
#     id: int


@g.app.post("/update_annotation")
async def update_annotation(request: Request, state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    # print(f'{updated=}')
    # content = await request.json()
    # d = content.get('payload', {})
    print(f'{state=}')


@g.app.on_event("startup")
async def startup_event():
    print("startup_event --- init something before server starts")


@g.app.get('/favicon.ico')
async def favicon():
    return FileResponse('./icon.png')

if __name__ == "__main__":
    uvicorn.run(g.app, host="0.0.0.0", port=8000)

