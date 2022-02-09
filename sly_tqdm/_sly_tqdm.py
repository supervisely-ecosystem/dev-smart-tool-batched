import asyncio
import copy
import re

from asgiref.sync import async_to_sync
from tqdm import tqdm

from supervisely.app import DataJson


def extract_by_regexp(regexp, string):
    result = re.search(regexp, string)
    if result is not None:
        return result.group(0)
    else:
        return ''


class _slyProgressBarIO:
    def __init__(self, identifier, message=None, total_provided=None):
        self.data = DataJson()
        self.identifier = identifier

        self.progress = {
            'percent': 0,
            'info': '',
            'message': message,
            'status': None
        }

        self.prev_state = self.progress.copy()
        self.total_provided = total_provided

    def write(self, s):
        print(s)
        new_text = s.strip().replace('\r', '')
        if len(new_text) != 0:
            if self.total_provided:
                self.progress['percent'] = int(extract_by_regexp(r'\d*\%', new_text).replace('%', ''))
                self.progress['info'] = extract_by_regexp(r'(\d+(?:\.\d+\w+)?)*/.*\]', new_text)
            else:
                self.progress['percent'] = 50
                self.progress['info'] = extract_by_regexp(r'(\d+(?:\.\d+\w+)?)*.*\]', new_text)

    def flush(self):
        if self.prev_state != self.progress:
            if self.progress['percent'] != '0' and self.progress['percent'] != '' and self.progress['info'] != '':

                for key, value in self.progress.items():
                    self.data['widgets'][f'{self.identifier}'][key] = value

                async_to_sync(self.data.synchronize_changes)()

                self.prev_state = copy.deepcopy(self.progress)

    def __del__(self):
        self.data['widgets'][f'{self.identifier}']['status'] = "success"
        self.data['widgets'][f'{self.identifier}']['percent'] = 100

        async_to_sync(self.data.synchronize_changes)()


class sly_tqdm(tqdm):
    def __init__(self, iterable=None, identifier=None, message=None, desc=None, total=None, leave=True, ncols=None,
                 mininterval=1.0, maxinterval=10.0, miniters=None, ascii=False, disable=False, unit='it',
                 unit_scale=False, dynamic_ncols=False, smoothing=0.3, bar_format=None, initial=0, position=None,
                 postfix=None, unit_divisor=1000, gui=False, **kwargs):
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

        total_provided = True if (iterable is not None and len(iterable) is not None) or total is not None else False

        sly_io = _slyProgressBarIO(identifier, message, total_provided)

        super().__init__(iterable=iterable, desc=desc, total=total, leave=leave, file=sly_io, ncols=ncols,
                         mininterval=mininterval,
                         maxinterval=maxinterval, miniters=miniters, ascii=ascii, disable=disable, unit=unit,
                         unit_scale=unit_scale, dynamic_ncols=dynamic_ncols, smoothing=smoothing, bar_format=bar_format,
                         initial=initial, position=position, postfix=postfix, unit_divisor=unit_divisor,
                         gui=gui, **kwargs)

    @staticmethod
    def to_html(identifier=None, message=None):
        if identifier is None:
            return f"<p style='background-color: darkred; color: white;'>" \
                   f"<b>{sly_tqdm.__name__}</b> missing 1 required positional argument: <b>'identifier'</b>" \
                   f"</p>"

        if DataJson()['widgets'].get(f'{identifier}') is None:
            data = DataJson()
            data['widgets'][f'{identifier}'] = {
                'percent': 0,
                'info': None,
                'message': message,
                'status': None
            }

        return '''
        <div id="{0}">
                <div style="display: flex; flex-direction: column">
                    <div style="display: flex; flex-direction: row; justify-content: space-between;
                      margin: 10px 4px">
                        <div v-if="data.widgets.{0}.message" style="margin: 0 0;
                                                                    background: #3266a8;
                                                                    color: white;
                                                                    font-weight: 500;
                                                                    border-radius: 8px;
                                                                    padding: 9px 18px;
                                                                    transition: .5s box-shadow, .5s opacity, .5s background !important;
                                                                    text-transform: uppercase;
                                                                    font-size: 13px;">
                            {{{{ data.widgets.{0}.message }}}}
                        </div>
                        <div v-if="data.widgets.{0}.info" style="margin: 0 8px;
                                                                    background: #9039bb;
                                                                    color: white;
                                                                    font-weight: 500;
                                                                    border-radius: 8px;
                                                                    padding: 9px 18px;
                                                                    transition: .5s box-shadow, .5s opacity, .5s background !important;
                                                                    text-transform: uppercase;
                                                                    font-size: 13px;">
                            {{{{ data.widgets.{0}.info }}}}
                        </div>
                    </div>

                    <el-progress :percentage="data.widgets.{0}.percent" :status="data.widgets.{0}.status"
                    style="margin-left:5px"></el-progress>
                </div>
            </div>
            '''.format(identifier)
