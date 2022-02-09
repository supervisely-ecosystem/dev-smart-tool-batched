import os
import sys
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

import supervisely
from supervisely.app import DataJson, LastStateJson
from supervisely.app.fastapi import create, Jinja2Templates

app_dir = str(Path(sys.argv[0]).parents[1])
print(f"App root directory: {app_dir}")

app = FastAPI()

sly_app = create()
app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory="../static"), name="static")

address = 'https://supervisely-dev.deepsystems.io/'
token = os.environ['API_TOKEN']
api = supervisely.Api(address, token)

LastStateJson({

    'widgets': {
        'smartToolSegWidget':
            {
                'identifier': None,
                'imageUrl': 'https://supervisely-dev.deepsystems.io/image-converter/convert/h5un6l2bnaz1vj8a9qgms4-public/images/original/7/h/Vo/9DJXpviU3WfWBv3b8rz6umnz6qnuRvBdU7xFbYKqK1uihMqNNCkAlqMViGM7jxp0CeoswqkpffSwC1XUoV80MdXMkhETuGfDkvSGKj4Nst2S6wJUyT5b8fTHCm2U.jpg?1589882430061',
                'positivePoints': [],
                'negativePoints': [],
                'bbox': [[530, 200], [930, 460]],
                'mask': None,
                'isActive': True
            }
    },

})

DataJson(
    {
        'widgets': {},

    }
)

templates_env = Jinja2Templates(directory="../templates")
