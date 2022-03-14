from supervisely.app import DataJson
from src.select_class.local_widgets import classes_table

import src.sly_globals as g


def init_table_data():
    rows_to_init = []
    for label, queue in g.classes2queues.items():
        rows_to_init.append([label, len(queue.queue), len(queue.queue)])

    classes_table.rows = rows_to_init


def update_classes_table():
    actual_rows = classes_table.rows

    labels = list(g.classes2queues.keys())
    queues = list(g.classes2queues.values())

    for row in actual_rows:
        label = row[0]
        row[1] = len(queues[labels.index(label)].queue)

    classes_table.rows = actual_rows
