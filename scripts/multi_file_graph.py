import os
import numpy as np
import matplotlib.pyplot as plt
from data_extraction import *

def aggregate_mean_time_series_fast(vectors, key, convert_to_ms=False):
    valid_modules = []
    all_times_list = []
    for module, metric_dict in vectors.items():
        if key in metric_dict:
            valid_modules.append(module)
            for times, values in metric_dict[key]:
                all_times_list.extend(times)

    if not valid_modules:
        return np.array([]), np.array([])

    all_times = np.unique(all_times_list)
    if len(all_times) == 0:
        return np.array([]), np.array([])

    sum_values = np.zeros_like(all_times, dtype=float)
    count_values = np.zeros_like(all_times, dtype=float)

    for module in valid_modules:
        for times, values in vectors[module][key]:
            times = np.array(times, dtype=float)
            values = np.array(values, dtype=float)
            if len(times) > 1:
                interpolated = np.interp(all_times, times, values)
            else:
                if len(values) > 0:
                    interpolated = np.full_like(all_times, values[0])
                else:
                    interpolated = np.zeros_like(all_times)

            sum_values += interpolated
            count_values += 1.0

    with np.errstate(divide='ignore', invalid='ignore'):
        mean_values = np.divide(
            sum_values, 
            count_values, 
            out=np.zeros_like(sum_values),
            where=(count_values != 0)
        )

    if convert_to_ms:
        mean_values *= 1000.0

    return all_times, mean_values

def plot_graph(file_list,SUBSAMPLE_NUMBER, SUBSAMPLE_RATE, QUEUE_Y_LIMITS, RESPONSE_Y_LIMITS, X_LIMIT):

    all_times_rt = []
    all_values_rt = []
    all_labels_rt = []

    all_times_ql = []
    all_values_ql = []
    all_labels_ql = []

    for json_file in file_list:
        params = parse_filename(json_file)
        dist = params["distribution"]
        opz = params["opzione"]
        iat = params["interarrival"]
        

        label_str = f"{dist}, Option {opz}, λ={iat}"

        file_name = f"data/{json_file}"
        data = load_data(file_name)
        scalars, vectors = extract_statistics(
            data,
            subsample_rate=SUBSAMPLE_RATE,
            subsample_number=SUBSAMPLE_NUMBER
        )

        rt_times, rt_values = aggregate_mean_time_series_fast(
            vectors, "responseTime:vector", convert_to_ms=True
        )
        ql_times, ql_values = aggregate_mean_time_series_fast(
            vectors, "queueLength:vector", convert_to_ms=False
        )

        if X_LIMIT is not None:
            (t_min, t_max) = X_LIMIT

            rt_idx = (rt_times >= t_min) & (rt_times <= t_max)
            rt_times = rt_times[rt_idx]
            rt_values = rt_values[rt_idx]

            ql_idx = (ql_times >= t_min) & (ql_times <= t_max)
            ql_times = ql_times[ql_idx]
            ql_values = ql_values[ql_idx]

        all_times_rt.append(rt_times)
        all_values_rt.append(rt_values)
        all_labels_rt.append(label_str)

        all_times_ql.append(ql_times)
        all_values_ql.append(ql_values)
        all_labels_ql.append(label_str)

    plt.figure(figsize=(10, 6))
    for times, vals, label in zip(all_times_rt, all_values_rt, all_labels_rt):
        if len(times) > 0:
            plt.plot(times, vals, label=label)

    plt.title("Aggregated Response Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Response Time (ms)")
    plt.grid(True, linestyle="--", alpha=0.7)

    if RESPONSE_Y_LIMITS is not None:
        plt.ylim(RESPONSE_Y_LIMITS)
    if X_LIMIT is not None:
        plt.xlim(X_LIMIT)

    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10, 6))
    for times, vals, label in zip(all_times_ql, all_values_ql, all_labels_ql):
        if len(times) > 0:
            plt.plot(times, vals, label=label)

    plt.title("Aggregated Queue Length")
    plt.xlabel("Time (s)")
    plt.ylabel("Queue Length")
    plt.grid(True, linestyle="--", alpha=0.7)

    if QUEUE_Y_LIMITS is not None:
        plt.ylim(QUEUE_Y_LIMITS)
    if X_LIMIT is not None:
        plt.xlim(X_LIMIT)

    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    
    file_list = [
        #"Uniform_A_N250_I01_S1e3.json",
        #"Uniform_A_N250_I05_S1e3.json",
        #"Lognormal_A_N250_I01_S1e3.json",
        "Lognormal_A_N250_I05_S1e3.json",
        #"Uniform_B_N250_I01_S1e3.json",
        #"Uniform_B_N250_I05_S1e3.json",
        #"Lognormal_B_N250_I01_S1e3.json",
        "Lognormal_B_N250_I05_S1e3.json",
    ]

    SUBSAMPLE_NUMBER = 100
    SUBSAMPLE_RATE = 90
    QUEUE_Y_LIMITS = (0, 60)
    RESPONSE_Y_LIMITS = (0, 200)
    X_LIMIT = (100, 900)
    
    plot_graph(file_list,SUBSAMPLE_NUMBER, SUBSAMPLE_RATE, QUEUE_Y_LIMITS, RESPONSE_Y_LIMITS, X_LIMIT)
