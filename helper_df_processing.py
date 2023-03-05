import pandas as pd
import math


def binning_rect(df, col_name, bin_size):
    # Group df into rectangular bins, each bin containing the count of each class
    class_list = sorted(df[col_name["c"]].unique())
    for i, class_id in enumerate(class_list):
        df_c = df.loc[df[col_name["c"]] == class_id]
        x = df_c[col_name["x"]].values
        y = df_c[col_name["y"]].values
        q = (x + bin_size["x"] / 2) / bin_size["x"]
        q = [int(x) for x in q]
        r = (y + bin_size["y"] / 2) / bin_size["y"]
        r = [int(y) for y in r]
        df_c_axial = pd.DataFrame(dict(r=r, q=q))
        bins_c = df_c_axial.groupby(["q", "r"]).size().to_frame(name=str(class_id))
        if i == 0:
            bins = bins_c
        else:
            bins = pd.concat([bins, bins_c], axis=1).fillna(0)
    return bins


def scale_count(df, type="linear"):
    if type == "log":
        return df.applymap(log_scaling_count)
    elif type == "sqrt":
        return df.applymap(sqrt_scaling_count)
    else:
        return df


def log_scaling_count(count):
    # adding 1 to return non zero value for count=1
    return math.log(count + 1)


def sqrt_scaling_count(count):
    return math.sqrt(count)
