from supervisely.app import widgets

notification_box = widgets.NotificationBox(
    title='Project with same output name founded',
    description=
    '''
    Output project with name
        <a href="https://supervisely-dev.deepsystems.io/projects/{}/datasets"
                       target="_blank">{}</a> already exists.<br>
        Do you want to use existing project or create a new?
    '''
)

datasets_progress = widgets.SlyTqdm()
images_progress = widgets.SlyTqdm()
