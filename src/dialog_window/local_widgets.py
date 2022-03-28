from supervisely.app import widgets

notification_box = widgets.NotificationBox(
    title='',
    description=''

)

datasets_progress = widgets.SlyTqdm(message='starting download datasets...')
images_progress = widgets.SlyTqdm(message='starting download images...')
