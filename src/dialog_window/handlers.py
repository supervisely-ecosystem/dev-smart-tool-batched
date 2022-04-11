from supervisely.app.fastapi import run_sync

import src.dialog_window as dialog_window

import supervisely
from fastapi import Request, Depends

from supervisely.app import DataJson


def spawn_unsaved_mask_dialog(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    dialog_window.notification_box.title = 'Unsaved masks founded.'
    dialog_window.notification_box.description = 'You can upload masks in the current version or apply the changes first.'
    state['dialogWindowUnsavedMasks'] = True

    run_sync(DataJson().synchronize_changes())
    run_sync(state.synchronize_changes())
