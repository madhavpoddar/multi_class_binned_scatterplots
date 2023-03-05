from os.path import dirname, join, basename
import pandas as pd
import time

import pickle


class start_end:
    def __init__(self, start_statement):
        self.start = time.time()
        print(start_statement, end="... ")

    def done(self):
        print("Done (" + str(round(time.time() - self.start, 2)) + "s)")


def print_df_properties(df):
    print("Index names: " + str(df.index.names))
    print("Column names: " + str(df.columns.values))
    print("Row count: " + str(len(df.index)) + "\n")
    print("Index - Count of unique values: ")
    for i in range(len(df.index.names)):
        print(df.index.names[i] + ": " + str(len(df.index.unique(level=i))))


def datafile_path(filename):
    return join("data", filename)


def read_csv_file(filename, index_cols=None, display_df_properties=False):
    read_csv_se = start_end("Reading " + datafile_path(filename))
    df = pd.read_csv(datafile_path(filename))
    if index_cols != None:
        df.set_index(index_cols, inplace=True)
        df = df.sort_index()
    if display_df_properties:
        print_df_properties(df)
    read_csv_se.done()
    return df


def rename_column_names(df, X_dict):
    df = df.rename(
        columns=lambda x: X_dict[x.upper()] if x.upper() in X_dict.keys() else x
    )


def save_obj(obj, obj_name):
    with open(datafile_path(obj_name + ".pckl"), "wb") as f:
        pickle.dump(obj, f)


def load_obj(obj_name):
    with open(datafile_path(obj_name + ".pckl"), "rb") as f:
        obj = pickle.load(f)
    return obj


def get_quantiles(df):
    df_q = [None] * 5
    df_q[1] = df.quantile(q=0.25)
    df_q[2] = df.quantile(q=0.5)
    df_q[3] = df.quantile(q=0.75)

    ff_train_iqr = df_q[3] - df_q[1]
    df_q[4] = df_q[3] + 1.5 * ff_train_iqr
    df_q[0] = df_q[1] - 1.5 * ff_train_iqr

    df_qmin = df.quantile(q=0.00)
    df_qmax = df.quantile(q=1.00)

    for col_name in df.columns.values:
        # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
        df_q[4][col_name] = min(df_qmax[col_name], df_q[4][col_name])
        df_q[0][col_name] = max(df_qmin[col_name], df_q[0][col_name])

    return df_q


def get_quantiles_4(df):

    # ====================== #
    # Quantiles order:       #
    # -------------- Outlier # q_level[0]
    # max(q0.00, q0.25-IQR)  # df_q[0]
    # ----------------- Stem # q_level[1]
    # q0.25                  # df_q[1]
    # ------------------ Box # q_level[2]
    # q0.75                  # df_q[2]
    # ----------------- Stem # q_level[3]
    # min(q1.00, q0.75+IQR)  # df_q[3]
    # -------------- Outlier # q_level[4]
    # ====================== #

    df_q = [None] * 4
    df_q[1] = df.quantile(q=0.25)
    df_q[2] = df.quantile(q=0.75)

    ff_train_iqr = df_q[2] - df_q[1]
    df_q[3] = df_q[2] + 1.5 * ff_train_iqr
    df_q[0] = df_q[1] - 1.5 * ff_train_iqr

    df_qmin = df.quantile(q=0.00)
    df_qmax = df.quantile(q=1.00)

    for col_name in df.columns.values:
        # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
        df_q[3][col_name] = min(df_qmax[col_name], df_q[3][col_name])
        df_q[0][col_name] = max(df_qmin[col_name], df_q[0][col_name])

    return df_q


def q_level_element(ele, q_4, col_name):
    # For non-linear color mapping we assign q_levels as 0, 2, 3, 4, 6 instead or 0, 1, 2, 3, 4
    q_levels = [0, 2, 3, 4, 6]
    q_level = q_levels[4]
    for i in range(4):
        if ele < q_4[i][col_name]:
            q_level = q_levels[i]
            break
    return q_level


def generate_q_level_df(df, q_4):
    q_level_df = df.copy()
    for col_name in df.columns.values:
        q_level_df[col_name] = q_level_df[col_name].apply(
            q_level_element, args=(q_4, col_name)
        )
    return q_level_df
