import asyncio
import functools
from threading import Thread

import uvicorn  # 🪐 server tools
from fastapi import Request, Depends

import supervisely
from smart_tool import SmartTool  # 🤖 widgets

import initialize_app
import src.sly_globals as g
from supervisely.app import StateJson


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request,
                                                           'smart_tool': SmartTool})


@g.app.on_event("startup")
def startup_event():
    initialize_app.init_routes()
    initialize_app.init_project()

    # await task
    print("startup_event --- init something before server starts")


uvicorn.run(g.app, host="127.0.0.1", port=8000)
