import asyncio
import copy
import functools
import re
from pathlib import Path
from uuid import uuid4

import markupsafe
from asgiref.sync import async_to_sync
from jinja2 import Environment

from supervisely.app import StateJson, LastStateJson, DataJson
from supervisely.app.jinja2 import create_env


class SmartTool:
    def __init__(self, app, state, data):
        self.app = app
        self.identifier = self.get_widget_identifier(state, data)

        self.widget_data = {
            'identifier': f'{self.identifier}',
            'imageUrl': 'https://supervisely-dev.deepsystems.io/image-converter/convert/h5un6l2bnaz1vj8a9qgms4-public/images/original/7/h/Vo/9DJXpviU3WfWBv3b8rz6umnz6qnuRvBdU7xFbYKqK1uihMqNNCkAlqMViGM7jxp0CeoswqkpffSwC1XUoV80MdXMkhETuGfDkvSGKj4Nst2S6wJUyT5b8fTHCm2U.jpg?1589882430061',
            'imageHash': '',
            'positivePoints': [],
            'negativePoints': [],
            'bbox': [[200, 200], [400, 400]],
            'mask': None,
            'isActive': True
        }
        self.update_remote_fields(state, data)

    def update_remote_fields(self, state, data):
        state['widgets'].setdefault(f'{self.__class__.__name__}', {})[f'{self.identifier}'] = self.widget_data
        async_to_sync(state.synchronize_changes)()

    def remove_remote_fields(self, state, data):
        existing_objects = state['widgets'].get(f'{self.__class__.__name__}', {})
        if existing_objects.get(self.identifier, None) is not None:
            existing_objects.pop(self.identifier)
            async_to_sync(state.synchronize_changes)()

    def get_widget_identifier(self, state, data):
        existing_widgets_count = len(state["widgets"].get(f'{self.__class__.__name__}', []))
        return f'{existing_widgets_count:04d}'

    def to_html(self):
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)

        html = jinja2_sly_env.get_template("smart_tool.html").render(identifier=self.identifier)
        return markupsafe.Markup(html)

    @staticmethod
    def to_undefined_html():
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)

        html = jinja2_sly_env.get_template("smart_tool.html").render()
        return markupsafe.Markup(html)





