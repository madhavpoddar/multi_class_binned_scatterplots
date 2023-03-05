import numpy as np
import pandas as pd

from helper_functions import read_csv_file


def get_dataset_names():
    return ["2d_uniform_data", "smallbump_data", "covtype", "covtype_2"]


def generate_2d_uniform_data(N, class_2_ratio, low, high, bin_size):
    N = 500000
    uniform_data = np.random.uniform(low=low, high=high, size=(N, 2))
    bin_size = {"x": bin_size[0], "y": bin_size[1]}
    uniform_data = np.hstack((uniform_data, np.ones((N, 1))))
    df = pd.DataFrame(data=uniform_data, columns=["x_col", "y_col", "c_col"])
    df.loc[df.tail(int(N * class_2_ratio)).index, "c_col"] = 2
    col_name = {"x": "x_col", "y": "y_col", "c": "c_col"}
    return df, col_name, bin_size


def generate_2d_smallbump_data(bin_size):
    # make this example reproducible
    np.random.seed(1)
    range_start_x = 0
    range_finish_x = 10
    range_y = [0, 100, 200, 300]

    # generating sample data
    data_normalized_x_c1 = np.random.normal(
        loc=(range_start_x + range_finish_x) / 2,
        scale=(range_finish_x - range_start_x) / 10,
        size=3000,
    )
    data_random_x_c1_part1 = np.random.uniform(range_start_x, range_finish_x, 20000)
    data_x_c1_part1 = np.concatenate([data_normalized_x_c1, data_random_x_c1_part1])
    data_y_c1_part1 = np.random.uniform(range_y[1], range_y[2], len(data_x_c1_part1))

    data_random_x_c1_part0 = np.random.uniform(range_start_x, range_finish_x, 23000)
    data_x_c1_part0 = np.concatenate([data_random_x_c1_part0])
    data_y_c1_part0 = np.random.uniform(range_y[0], range_y[1], len(data_x_c1_part0))

    data_random_x_c1_part2 = np.random.uniform(range_start_x, range_finish_x, 23000)
    data_x_c1_part2 = np.concatenate([data_random_x_c1_part2])
    data_y_c1_part2 = np.random.uniform(range_y[2], range_y[3], len(data_x_c1_part2))

    data_x_c1 = np.concatenate([data_x_c1_part0, data_x_c1_part1, data_x_c1_part2])
    data_y_c1 = np.concatenate([data_y_c1_part0, data_y_c1_part1, data_y_c1_part2])

    data_random_x_c2 = np.random.uniform(range_start_x, range_finish_x, 75000)
    data_x_c2 = data_random_x_c2
    data_y_c2 = np.random.uniform(range_y[0], range_y[-1], len(data_x_c2))

    data_x = np.concatenate([data_x_c1, data_x_c2])
    data_y = np.concatenate([data_y_c1, data_y_c2])
    # data_c = np.concatenate([np.ones(len(data_x_c1)), np.ones(len(data_x_c2)) * 2])
    data_c = np.concatenate([["c1"] * len(data_x_c1), ["c2"] * len(data_x_c2)])

    # Random subsampling
    data_rs_x_c1 = np.random.choice(data_x_c1, int(len(data_x_c1) * 0.07))
    data_rs_y_c1 = np.random.choice(data_y_c1, len(data_rs_x_c1))
    data_rs_x_c2 = np.random.choice(data_x_c2, int(len(data_x_c2) * 0.07))
    data_rs_y_c2 = np.random.choice(data_y_c2, len(data_rs_x_c2))

    df = pd.DataFrame(
        data=np.array((data_x, data_y, data_c)).T, columns=["X", "Y", "c_col"],
    )
    col_name = {"x": "X", "y": "Y", "c": "c_col"}
    bin_size = {"x": bin_size[0], "y": bin_size[1]}
    return df, col_name, bin_size


def get_data(name):
    if name not in get_dataset_names():
        print("Invalid dataset name.")
        return None, None, None
    if name == "2d_uniform_data":
        df, col_name, bin_size = generate_2d_uniform_data(
            5000, 0.2, [-1, -1], [1, 1], [0.1, 0.1]
        )
    elif name == "smallbump_data":
        df, col_name, bin_size = generate_2d_smallbump_data([1, 100])
    elif name == "covtype":
        df = read_csv_file("covtype.csv")
        col_name = {
            "x": "Horizontal_Distance_To_Hydrology",
            "y": "Vertical_Distance_To_Hydrology",
            "c": "Cover_Type",
        }
        bin_size = {"x": 50, "y": 50}
    elif name == "covtype_2":
        df = read_csv_file("covtype.csv")
        col_name = {
            "x": "Elevation",
            "y": "Horizontal_Distance_To_Hydrology",
            "c": "Cover_Type",
        }
        bin_size = {"x": 50, "y": 50}
    return df, col_name, bin_size
