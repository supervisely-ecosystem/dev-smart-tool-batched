import supervisely.app.widgets as widgets

classes_table = widgets.RadioTable(
    columns=["classname", "left", "total"],
    rows=[],
    subtitles={},  # {"name": "subname"},
    column_formatters={},
)

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
