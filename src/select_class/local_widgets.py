import supervisely.app.widgets as widgets


def progress_bar_formatter(value):
    return f'''<el-progress 
                    :percentage="{value}" 
                    :text-inside="true"
                    :stroke-width="18" style="width: 320px">
                    </el-progress>'''


classes_table = widgets.RadioTable(
    columns=["classname", "left", "total", "progress"],
    rows=[],
    subtitles={},  # {"name": "subname"},
    column_formatters={
        'progress': progress_bar_formatter
    },
)

images_table = widgets.RadioTable(
    columns=["classname", "left", "total", "progress"],
    rows=[],
    subtitles={},
    column_formatters={
        'progress': progress_bar_formatter
    },
)


