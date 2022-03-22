import supervisely.app.widgets as widgets


def progress_bar_formatter(value):
    return f'''<el-progress :percentage="{value}" style="width: 220px"></el-progress>'''


classes_table = widgets.RadioTable(
    columns=["classname", "left", "total", "progress"],
    rows=[],
    subtitles={},  # {"name": "subname"},
    column_formatters={
        'progress': progress_bar_formatter 
    },
)


