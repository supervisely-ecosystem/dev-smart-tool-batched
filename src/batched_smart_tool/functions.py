
import src.sly_globals as g


def update_local_masks(response):
    for index, widget in enumerate(g.grid_controller.widgets.values()):
        data = response.get(f'{index}')
        if data is not None:
            widget.mask = {
                'data': data.get('bitmap'),
                'origin': [data['origin']['x'], data['origin']['y']],
                'color': '#77e377'
            }


def add_point_to_active_cards(origin_identifier, updated_point, points_type):
    new_connected_points = set()

    for widget in g.grid_controller.widgets.values():
        if widget.is_active and widget.identifier != origin_identifier:
            point_id = widget.update_by_relative_coordinates(updated_point, points_type)

            if point_id is not None:
                new_connected_points.add(point_id)

    new_connected_points.add(updated_point['id'])

    for widget in g.grid_controller.widgets.values():
        if widget.is_active:
            widget.add_connected_point(connected_points_ids=new_connected_points)


def remove_point_from_connected_cards(origin_identifier, point_to_remove, points_type):
    for widget in g.grid_controller.widgets.values():
        if widget.identifier != origin_identifier:
            widget.remove_connected_point(point_to_remove, points_type)


def get_data_to_process():
    data_to_send = {}
    for index, widget in enumerate(g.grid_controller.widgets.values()):
        if widget.needs_an_update:
            widget.needs_an_update = False

            widget_data = widget.get_data_to_send()
            data_to_send[index] = \
                {
                    "crop": [
                        {
                            "x": widget_data['bbox'][0][0],
                            "y": widget_data['bbox'][0][1]
                        },
                        {
                            "x": widget_data['bbox'][1][0],
                            "y": widget_data['bbox'][1][1]
                        }
                    ],
                    "positive": [
                        {
                            "x": positive_point['position'][0][0],
                            "y": positive_point['position'][0][1]
                        } for positive_point in widget_data['positivePoints']
                    ],
                    "negative": [
                        {
                            "x": negative_points['position'][0][0],
                            "y": negative_points['position'][0][1]
                        } for negative_points in widget_data['negativePoints']
                    ],
                    "image_hash": f"{widget_data['imageHash']}"
                }

    return data_to_send
