from supervisely.app import DataJson
from src.select_class.local_widgets import classes_table, images_table

import src.sly_globals as g


def init_table_data():
    rows_to_init = []
    for label, queue in g.classes2queues.items():
        rows_to_init.append([label, len(queue.queue), len(queue.queue), 0])

    classes_table.rows = rows_to_init

    images_table.rows = [
        ['image', len(g.images_queue.queue), len(g.images_queue.queue), 0]
    ]


def update_classes_table():
    actual_rows = classes_table.rows

    labels = list(g.classes2queues.keys())
    queues = list(g.classes2queues.values())

    for row in actual_rows:
        label = row[0]
        if label == g.output_class_name:
            row[1] = len(queues[labels.index(label)].queue) + len(g.grid_controller.widgets)
        else:
            row[1] = len(queues[labels.index(label)].queue)

        row[3] = int(((row[2] - row[1]) / row[2]) * 100)

    classes_table.rows = actual_rows

    actual_rows = images_table.rows
    for row in actual_rows:

        if 'image' == g.output_class_name:
            row[1] = len(g.images_queue.queue) + len(g.grid_controller.widgets)
        else:
            row[1] = len(g.images_queue.queue)

        row[3] = int(((row[2] - row[1]) / row[2]) * 100)



