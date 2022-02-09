import os

import jinja2
from starlette.templating import Jinja2Templates

import sly_globals as g


async def get_widget_identifier_from_request(request):
    content = await request.json()
    payload = content.get('payload', {})
    identifier = payload.get('identifier')
    return identifier
