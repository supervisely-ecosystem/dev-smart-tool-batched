import asyncio
import copy
import re

from asgiref.sync import async_to_sync

from supervisely.app import StateJson, LastStateJson


class smart_tool:
    def __init__(self, identifier):
        """
        Wrapper for classic tqdm progress bar.

            Parameters
            ----------
            identifier  : int, required
                HTML element identifier
            message  : int, optional
                Text message which displayed in HTML


            desc, total, leave, ncols, ... :
                Like in tqdm

        """
        if identifier is None:
            raise ValueError('identifier must be initialized')

    @staticmethod
    def to_html(identifier=None):
        if identifier is None:
            return f"<p style='background-color: darkred; color: white;'>" \
                   f"<b>{smart_tool.__name__}</b> missing 1 required positional argument: <b>'identifier'</b>" \
                   f"</p>"

        if LastStateJson()['widgets'].get(f'{identifier}') is None:
            state = LastStateJson()
            state['widgets'][f'{identifier}'] = {
                'identifier': identifier,
                'imageUrl': 'https://supervisely-dev.deepsystems.io/image-converter/convert/h5un6l2bnaz1vj8a9qgms4-public/images/original/7/h/Vo/9DJXpviU3WfWBv3b8rz6umnz6qnuRvBdU7xFbYKqK1uihMqNNCkAlqMViGM7jxp0CeoswqkpffSwC1XUoV80MdXMkhETuGfDkvSGKj4Nst2S6wJUyT5b8fTHCm2U.jpg?1589882430061',
                'positivePoints': [],
                'negativePoints': [],
                'bbox': [[530, 200], [930, 460]],
                'mask': None,
                'isActive': True
            }

        return '''
        <div id="widgets-{0}">
                <vue-smart-seg-widget :data="state.widgets.{0}" :post="post"></vue-smart-seg-widget>
        </div>
        '''.format(identifier)
