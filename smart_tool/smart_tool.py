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
        self.data = data
        self.state = state

        self.identifier = self.get_widget_identifier()
        self.initialize_fields()


    def initialize_fields(self):
        data_placeholder = {
            'identifier': f'{self.identifier}',
            'imageUrl': 'https://supervisely-dev.deepsystems.io/image-converter/convert/h5un6l2bnaz1vj8a9qgms4-public/images/original/7/h/Vo/9DJXpviU3WfWBv3b8rz6umnz6qnuRvBdU7xFbYKqK1uihMqNNCkAlqMViGM7jxp0CeoswqkpffSwC1XUoV80MdXMkhETuGfDkvSGKj4Nst2S6wJUyT5b8fTHCm2U.jpg?1589882430061',
            'imageHash': '',
            'positivePoints': [],
            'negativePoints': [],
            'bbox': [[200, 200], [400, 400]],
            'mask': None,
            'isActive': True
        }

        self.state['widgets'].setdefault(f'{self.__class__.__name__}', {})[f'{self.identifier}'] = data_placeholder

        async_to_sync(self.state.synchronize_changes)()

    def get_widget_identifier(self):
        existing_widgets_count = len(self.state["widgets"].get(f'{self.__class__.__name__}', []))
        return f'{existing_widgets_count:04d}'

    def to_html(self):
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)

        html = jinja2_sly_env.get_template("smart_tool.html").render(identifier=self.identifier)
        return markupsafe.Markup(html)

    def _update_data(self, data_to_upload, state):
        for key, value in data_to_upload.items():
            state['widgets'][f'{self.identifier}'][key] = value

    @staticmethod
    def to_undefined_html():
        current_dir = Path(__file__).parent.absolute()
        jinja2_sly_env: Environment = create_env(current_dir)

        html = jinja2_sly_env.get_template("smart_tool.html").render()
        return markupsafe.Markup(html)



