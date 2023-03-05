import math
import random
from bokeh.plotting import figure, show
from bokeh.io import export_png
from bokeh.models import Range1d

from get_data import get_data
from helper_df_processing import binning_rect, scale_count


class visual_parameters:
    def __init__(
        self, bin_size, perfect_sq_sqrt, max_depth, marker_shape,
    ):
        # Visualization Parameters
        self.bin_size = bin_size
        self.perfect_sq_sqrt = perfect_sq_sqrt
        self.marker_shape = marker_shape
        self.perfect_sq = (
            perfect_sq_sqrt * perfect_sq_sqrt
        )  # each parent bubble is divided into these many child bubbles
        self.max_depth = max_depth  # max_depth = depth of bubble hierarchy or len(unique sizes of bubbles)-1
        self.sq_list = [int(self.perfect_sq ** i) for i in range(self.max_depth + 1)][
            ::-1
        ]
        # for eg., perfect_sq = 4, depth = 4, sq_list = [256, 64, 16, 4, 1]


def custom_round(a):
    if a < 1:
        return 1
    return round(a)


def compute_colors_divided_locations(values, colors, max_sum, vis_param):
    # normalizing values to 0-sq_list[0] range
    values = values * vis_param.sq_list[0] / max_sum
    # keep only non-zero values
    values, color = zip(*((x, y) for x, y in zip(values, colors) if x != 0))

    # rounding the values to fit the size of bubble(s)
    values = [custom_round(value) for value in values]
    # if sum of values exceeds sq_list[0], we reduce the maximum value by the difference
    if sum(values) > vis_param.sq_list[0]:
        values[values.index(max(values))] -= sum(values) - vis_param.sq_list[0]

    values_divided = []
    colors_divided = []
    for v, c in zip(values, color):
        for sq in vis_param.sq_list:
            values_divided.extend([sq] * int(v / sq))
            colors_divided.extend([c] * int(v / sq))
            v -= int(v / sq) * sq

    values_divided, colors_divided = (
        list(t) for t in zip(*sorted(zip(values_divided, colors_divided), reverse=True))
    )
    colors_divided_locations = {}
    for sq in vis_param.sq_list:
        colors_divided_locations[sq] = [""] * int(vis_param.sq_list[0] / sq)

    for v, c in zip(values_divided, colors_divided):
        possible_indices = [
            i for i, x in enumerate(colors_divided_locations[v]) if x == ""
        ]
        index_v = random.choice(possible_indices)
        colors_divided_locations[v][index_v] = c

        index_v_smaller = int(index_v * vis_param.perfect_sq)
        v_smaller = int(v / vis_param.perfect_sq)

        while v_smaller > 0:
            colors_divided_locations[v_smaller][
                index_v_smaller : index_v_smaller + int(v / v_smaller)
            ] = [None] * int(v / v_smaller)
            index_v_smaller = int(index_v_smaller * vis_param.perfect_sq)
            v_smaller = int(v_smaller / vis_param.perfect_sq)

    return colors_divided_locations


def compute_bubble_radii(vis_param):
    # Computing radii of bubbles at different levels of hierarchy
    bubbles_radii = {}
    for sq in vis_param.sq_list:
        if sq == vis_param.sq_list[0]:
            # radius of biggest bubble covering the entire bin
            bubbles_radii[sq] = [
                vis_param.bin_size["x"] / 2,
                vis_param.bin_size["y"] / 2,
            ]
        else:
            # radius of children bubble calculated from the radius of parent bubble
            bubbles_radii[sq] = [
                x_or_y / vis_param.perfect_sq_sqrt
                for x_or_y in bubbles_radii[sq * vis_param.perfect_sq]
            ]
    return bubbles_radii


def compute_bubble_centres(bin_index, bubbles_radii, vis_param):
    # computing centres of bubbles:
    (bin_x_index, bin_y_index) = bin_index
    bubble_centres = {}
    for sq in vis_param.sq_list:
        bubble_centres[sq] = [None] * int(vis_param.sq_list[0] / sq)
    for sq in vis_param.sq_list:
        # The centre of bubble covering the entire bin is located at the centre of rectangular bin
        if sq == vis_param.sq_list[0]:
            bubble_centres[sq][0] = [
                bin_x_index * vis_param.bin_size["x"],
                bin_y_index * vis_param.bin_size["y"],
            ]
        else:
            for index in range(len(bubble_centres[sq])):
                # bubble centre of the child bubble is computed using the centre of parent bubble
                parent_bubble_centre = bubble_centres[sq * vis_param.perfect_sq][
                    int(index / vis_param.perfect_sq)
                ]
                modulus = index % vis_param.perfect_sq
                bubble_centres[sq][index] = [
                    sum(x)
                    for x in zip(
                        parent_bubble_centre,
                        [
                            bubbles_radii[sq][0]
                            * (
                                (modulus % vis_param.perfect_sq_sqrt) * 2
                                - vis_param.perfect_sq_sqrt
                                + 1
                            ),
                            bubbles_radii[sq][1]
                            * (
                                int(modulus / vis_param.perfect_sq_sqrt) * 2
                                - vis_param.perfect_sq_sqrt
                                + 1
                            ),
                        ],
                    )
                ]
    return bubble_centres


def rect_binned_sp_scattered_bubbles(
    p,
    df,
    col_name,
    bin_size,
    colors,
    perfect_sq_sqrt: int = 2,
    max_depth: int = 3,
    marker_shape: str = "circle",
):

    vis_param = visual_parameters(bin_size, perfect_sq_sqrt, max_depth, marker_shape)
    bubbles_radii = compute_bubble_radii(vis_param)

    bins = binning_rect(df, col_name, bin_size)
    bins = scale_count(bins, "sqrt")
    max_sum = bins.sum(axis=1).max()
    class_labels = sorted(df[col_name["c"]].unique())
    for bin_index, values in bins.iterrows():
        colors_divided_locations = compute_colors_divided_locations(
            values, colors, max_sum, vis_param
        )
        bubble_centres = compute_bubble_centres(bin_index, bubbles_radii, vis_param)
        for sq in vis_param.sq_list:
            for index, c in enumerate(colors_divided_locations[sq]):
                if c not in [None, ""]:
                    if marker_shape in ["square", "rectangle"]:
                        p.quad(
                            top=[bubble_centres[sq][index][1] + bubbles_radii[sq][1]],
                            bottom=[
                                bubble_centres[sq][index][1] - bubbles_radii[sq][1]
                            ],
                            left=[bubble_centres[sq][index][0] + bubbles_radii[sq][0]],
                            right=[bubble_centres[sq][index][0] - bubbles_radii[sq][0]],
                            color=c,
                        )
                    elif marker_shape in ["circle", "ellipse"]:
                        p.ellipse(
                            [bubble_centres[sq][index][0]],
                            [bubble_centres[sq][index][1]],
                            height=bubbles_radii[sq][1] * 2,
                            width=bubbles_radii[sq][0] * 2,
                            fill_color=c,
                            line_width=0,
                        )


def main():
    p = figure(title="Scattered bubbles plot", width=1500, height=725)
    # left, right, bottom, top = 2700, 2900, 50, 150
    # p.x_range=Range1d(left, right)
    # p.y_range=Range1d(bottom, top)    
    p.grid.visible = False
    dataset_name = "covtype_2"
    df, col_name, bin_size = get_data(dataset_name)
    colors = [
        "#ff8c00",
        "#008000",
        "#dc143c",
        "#8a2be2",
        "#8b4513",
        "#ee82ee",
        "#483d8b",
    ]
    rect_binned_sp_scattered_bubbles(
        p, df, col_name, bin_size, colors,
    )
    p.xaxis.axis_label = col_name["x"]
    p.yaxis.axis_label = col_name["y"]

    show(p)


if __name__ == "__main__":
    main()
