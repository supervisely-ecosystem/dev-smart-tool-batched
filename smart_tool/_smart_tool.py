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
    def update_data(identifier, data_to_upload, state):
        for key, value in data_to_upload.items():
            state['widgets'][f'{identifier}'][key] = value

    @staticmethod
    def to_html(identifier=None):
        if identifier is None:
            return f"<p style='background-color: darkred; color: white;'>" \
                   f"<b>{smart_tool.__name__}</b> missing 1 required positional argument: <b>'identifier'</b>" \
                   f"</p>"

        if LastStateJson()['widgets'].get(f'{identifier}') is None:
            state = LastStateJson()
            state['widgets'][f'{identifier}'] = {
                'identifier': f'{identifier}',
                'imageUrl': '',
                'imageHash': '',
                'positivePoints': [],
                'negativePoints': [],
                'bbox': [],
                'mask': None,
                'isActive': True
            }

        return '''
        <div v-if="state.widgets[{0}].bbox.length > 0" id="widgets-{0}">
                <vue-smart-seg-widget :data="state.widgets[{0}]" :post="post"></vue-smart-seg-widget>
        </div>
        '''.format(identifier)
