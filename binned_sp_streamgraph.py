# from distutils.command.clean import clean
import numpy as np
import pandas as pd
import math
from copy import deepcopy

from bokeh.io import show
from bokeh.plotting import figure
from bokeh.layouts import column
from bokeh.models import Slider, Span
from bokeh.io import curdoc

from scipy import ndimage

from get_data import get_data


def gaussian_filter1d(size, sigma):
    filter_range = np.linspace(-int(size / 2), int(size / 2), size)
    gaussian_filter = [
        1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x**2) / (2 * sigma**2))
        for x in filter_range
    ]
    return gaussian_filter


def scaling_count(x):
    # if x == 0:
    # return 0
    # return math.sqrt(x)
    return int(x**1)


def cartesian_to_binned(x, y, bin_size):
    bin_x_id = [int(float(a) / bin_size["x"]) for a in x]
    bin_y_id = [int(float(a) / bin_size["y"]) for a in y]
    return bin_x_id, bin_y_id


def binning(df, col_name, bin_size):
    # Group df into hexagonal bins, each bin containing the count of each class
    class_list = sorted(df[col_name["c"]].unique())
    for i, class_id in enumerate(class_list):
        df_c = df.loc[df[col_name["c"]] == class_id]
        x = df_c[col_name["x"]].values
        y = df_c[col_name["y"]].values
        bin_x_id, bin_y_id = cartesian_to_binned(x, y, bin_size)
        df_c_binned = pd.DataFrame(dict(bin_x_id=bin_x_id, bin_y_id=bin_y_id))
        bins_c = (
            df_c_binned.groupby(["bin_x_id", "bin_y_id"])
            .size()
            .to_frame(name=str(class_id))
        )
        if i == 0:
            bins = bins_c
        else:
            bins = pd.concat([bins, bins_c], axis=1).fillna(0)
    return bins


def alpha_x_y_slider_update(attrname, old, new):
    global x_streams, y_streams
    for stream in y_streams:
        stream.glyph.fill_alpha = new
    for stream in x_streams:
        stream.glyph.fill_alpha = 1 - new


def create_binned_steamgraph_sp(
    p, df, col_name, bin_size, major_bin_axis, class_colors, overlapping=False
):
    if overlapping:
        padding_width_ratio = 0
    else:
        padding_width_ratio = 0.03
    min_width_ratio = 0.01

    minor_bin_axis = "y" if major_bin_axis == "x" else "x"

    bins = binning(df, col_name, bin_size)

    bins = bins.applymap(scaling_count)
    class_count = len(bins.columns)
    if overlapping:
        max_sum = bins.max().max() * 2
    else:
        max_sum = bins.sum(axis=1).max()
    padding_width = bin_size[major_bin_axis] * padding_width_ratio
    min_width = bin_size[major_bin_axis] * min_width_ratio
    ratio_height = (
        bin_size[major_bin_axis] - (class_count + 1) * padding_width
    ) / max_sum

    streams = []
    for bin_id_value in bins.index.unique(level="bin_" + major_bin_axis + "_id"):
        if major_bin_axis == "x":
            bins_selected_id = bins.loc[(bin_id_value, slice(None)), :].droplevel(
                level=0
            )
        else:
            bins_selected_id = bins.loc[(slice(None), bin_id_value), :].droplevel(
                level=1
            )

        range_x = range(
            int(bins_selected_id.index.values.min()),
            int(bins_selected_id.index.values.max()) + 1,
        )
        clean_data = pd.DataFrame(range_x).set_index(0)
        bins_selected_id = pd.concat([bins_selected_id, clean_data], axis=1).fillna(0)

        x = bins_selected_id.index.values
        x = x * bin_size[minor_bin_axis]
        x = x + [bin_size[minor_bin_axis] / 2] * len(x)
        ys = list(np.transpose(bins_selected_id.to_numpy()))

        # remove value layers which have sum count 0
        sum_count_individual_c = np.array([sum(x) for x in ys])
        colors = deepcopy(class_colors)
        class_list = list(bins.columns)
        for i in np.nonzero(sum_count_individual_c == 0)[0][::-1]:
            ys.pop(i)
            colors.pop(i)
            class_list.pop(i)

        ys = [ys_arr * ratio_height for ys_arr in ys]

        # Use this only if smoothing is necessary
        # ys = [ndimage.convolve1d(ys_arr, gaussian_filter1d(13, 2)) for ys_arr in ys]

        # Insert starting padding layer
        start_y = bin_id_value * bin_size[major_bin_axis]
        multiplier = 1
        if overlapping:
            multiplier = 0
        ys.insert(
            0,
            np.array(
                [
                    start_y
                    + bin_size[major_bin_axis] * 0.5
                    - (len(ys) - 1) * 0.5 * padding_width
                ]
                * len(ys[0])
            )
            - np.array([sum(x) / 2 for x in zip(*ys)]) * multiplier,
        )

        # insert padding layers between each layer of values
        padding_layer = [padding_width] * len(ys[0])

        for i in range(2, len(ys))[::-1]:
            ys.insert(i, padding_layer)

        if not overlapping:
            for i in range(1, len(ys)):
                ys[i] += ys[i - 1]

        for i in range(int(len(ys) / 2)):
            # add minimum width to highlight outliers / classes with low count
            if overlapping:
                for j in range(len(x)):
                    if ys[2 * i + 1][j] > 0 and ys[2 * i + 1][j] < min_width:
                        ys[2 * i + 1][j] = min_width
            else:
                for j in range(len(x)):
                    if (
                        ys[2 * i + 1][j] - ys[2 * i][j] > 0
                        and ys[2 * i + 1][j] - ys[2 * i][j] < min_width
                    ):
                        ys[2 * i + 1][j] = ys[2 * i][j] + min_width

            if overlapping:
                start_ys = -ys[2 * i + 1] + ys[0]
                end_ys = ys[2 * i + 1] + ys[0]
            else:
                start_ys = ys[2 * i]
                end_ys = ys[2 * i + 1]

            # drawing the stream area of a class
            if major_bin_axis == "x":
                stream = p.harea(
                    y=x,
                    x1=start_ys,
                    x2=end_ys,
                    color=colors[i],
                    alpha=0.5,
                    legend_label=str(class_list[i]),
                )
            else:
                stream = p.varea(
                    x=x,
                    y1=start_ys,
                    y2=end_ys,
                    color=colors[i],
                    alpha=0.5,
                    legend_label=str(class_list[i]),
                )

            dimension = "height" if major_bin_axis == "x" else "width"

            streams.append(stream)

            bin_border_lower = Span(
                location=start_y,
                dimension=dimension,
                line_color="lightgray",
                line_width=1,
                level="underlay",
            )
            bin_border_upper = Span(
                location=start_y + bin_size[major_bin_axis],
                dimension=dimension,
                line_color="lightgray",
                line_width=1,
                level="underlay",
            )
            p.renderers.extend([bin_border_lower, bin_border_upper])
            p.legend.click_policy = "hide"

    return streams


dataset_name = "covtype_2"
# dataset_name = "smallbump_data"
df, col_name, _ = get_data(dataset_name)
colors = [
    "#ff8c00",
    "#008000",
    "#dc143c",
    "#8a2be2",
    "#8b4513",
    "#ee82ee",
    "#073980",
]
# colors = [
#     "#0000ff",
#     "#ff3333",
# ]

p = figure(width=1000, height=700)
p.xaxis.axis_label = col_name["x"]
p.yaxis.axis_label = col_name["y"]
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# streams parallel to x-axis
bin_size = {"x": 20, "y": 200}
x_streams = create_binned_steamgraph_sp(
    p, df, col_name, bin_size, major_bin_axis="y", class_colors=colors
)

# streams parallel to y-axis
bin_size = {"x": 200, "y": 20}
y_streams = create_binned_steamgraph_sp(
    p, df, col_name, bin_size, major_bin_axis="x", class_colors=colors
)

alpha_x_y_slider = Slider(
    value=0.5,
    start=0,
    end=1,
    step=0.01,
)
alpha_x_y_slider.on_change("value", alpha_x_y_slider_update)
layout = column(p, alpha_x_y_slider)
curdoc().add_root(layout)
curdoc().title = "Streamgraph SP"
