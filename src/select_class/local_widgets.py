import supervisely.app.widgets as widgets

classes_table = widgets.RadioTable(
    columns=["classname", "left", "total"],
    rows=[],
    subtitles={},  # {"name": "subname"},
    column_formatters={},
)


