import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from data_extraction import *

def aggregate_mean_time_series(vectors, key, convert_to_ms=False):
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


def plot_graph(file_list,
               SUBSAMPLE_NUMBER,
               SUBSAMPLE_RATE,
               QUEUE_Y_LIMITS,
               RESPONSE_Y_LIMITS,
               X_LIMIT,
               boxplot_whiskers=None,
               boxplot_y_limits=None):

    if boxplot_whiskers is None:
        whiskers = 1.5
    else:
        whiskers = list(boxplot_whiskers)

    # --- Liste per i plot nel tempo di RT e QL ---
    all_times_rt = []
    all_values_rt = []
    all_labels_rt = []

    all_times_ql = []
    all_values_ql = []
    all_labels_ql = []

    # --- Liste per i boxplot di RT e QL ---
    boxplot_data_rt = []
    boxplot_data_ql = []
    boxplot_labels = []

    # --- Liste per i boxplot di forwarded e dropped ---
    boxplot_data_forwarded = []
    boxplot_data_dropped = []

    for json_file in file_list:
        params = parse_filename(json_file)
        dist = params["distribution"]
        opz = params["opzione"]
        iat = params["interarrival"]
        num_user = params["n_users"]
        size_rate = params["size_rate"]
        
        label_str = f"{dist}, Option {opz}, λ={iat}, N={num_user}, S={size_rate}"

        file_name = f"data/{json_file}"
        data = load_data(file_name)
        scalars, vectors = extract_statistics(
            data,
            subsample_rate=SUBSAMPLE_RATE,
            subsample_number=SUBSAMPLE_NUMBER
        )

        # --- Estraggo i dati per i grafici temporali di RT e QL ---
        rt_times, rt_values = aggregate_mean_time_series(
            vectors, "responseTime:vector", convert_to_ms=True
        )
        ql_times, ql_values = aggregate_mean_time_series(
            vectors, "queueLength:vector", convert_to_ms=False
        )

        # --- Applico eventuali limiti sull'asse x ---
        if X_LIMIT is not None:
            (t_min, t_max) = X_LIMIT

            rt_idx = (rt_times >= t_min) & (rt_times <= t_max)
            rt_times = rt_times[rt_idx]
            rt_values = rt_values[rt_idx]

            ql_idx = (ql_times >= t_min) & (ql_times <= t_max)
            ql_times = ql_times[ql_idx]
            ql_values = ql_values[ql_idx]

        # --- Accumulo i dati per i plot nel tempo ---
        all_times_rt.append(rt_times)
        all_values_rt.append(rt_values)
        all_labels_rt.append(label_str)

        all_times_ql.append(ql_times)
        all_values_ql.append(ql_values)
        all_labels_ql.append(label_str)

        # --- Accumulo i dati per i boxplot di RT e QL ---
        boxplot_data_rt.append(rt_values)
        boxplot_data_ql.append(ql_values)
        boxplot_labels.append(label_str)

        # --- Estrazione dei pacchetti forwardati e droppati dalle base station ---
        forwarded_list = []
        dropped_list = []

        # "scalars" ha la forma: { 'EdgeComputingNetwork.baseStations[0]': {'forwarded:count': [...], 'dropped:count': [...], ... }, ... }
        for module_name, metric_dict in scalars.items():
            if "forwarded:count" in metric_dict:
                # Aggiungo tutti i valori di forwarded:count per questa base station
                forwarded_list.extend(metric_dict["forwarded:count"])
            if "dropped:count" in metric_dict:
                dropped_list.extend(metric_dict["dropped:count"])

        boxplot_data_forwarded.append(forwarded_list)
        boxplot_data_dropped.append(dropped_list)

    # --- Plot: Aggregated Response Time ---
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

    # --- Plot: Aggregated Queue Length ---
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

    # --- Boxplot per Response Time ---
    colors_rt = plt.cm.tab10(np.linspace(0, 1, len(boxplot_data_rt)))
    plt.figure(figsize=(10, 6))
    bp_rt = plt.boxplot(
        boxplot_data_rt,
        whis=whiskers,
        patch_artist=True
    )
    for patch, color in zip(bp_rt['boxes'], colors_rt):
        patch.set_facecolor(color)
    handles_rt = []
    for color, label in zip(colors_rt, boxplot_labels):
        handles_rt.append(mpatches.Patch(color=color, label=label))
    plt.legend(handles=handles_rt)
    plt.title("Boxplot Response Time (ms)")
    plt.ylabel("Response Time (ms)")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()

    # --- Boxplot per Queue Length ---
    colors_ql = plt.cm.tab10(np.linspace(0, 1, len(boxplot_data_ql)))
    plt.figure(figsize=(10, 6))
    bp_ql = plt.boxplot(
        boxplot_data_ql,
        whis=whiskers,
        patch_artist=True
    )
    for patch, color in zip(bp_ql['boxes'], colors_ql):
        patch.set_facecolor(color)
    handles_ql = []
    for color, label in zip(colors_ql, boxplot_labels):
        handles_ql.append(mpatches.Patch(color=color, label=label))
    plt.legend(handles=handles_ql)
    plt.title("Boxplot Queue Length")
    plt.ylabel("Queue Length")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()

    # --- Boxplot per pacchetti forwardati ---
    colors_fwd = plt.cm.tab10(np.linspace(0, 1, len(boxplot_data_forwarded)))
    plt.figure(figsize=(10, 6))
    bp_fwd = plt.boxplot(
        boxplot_data_forwarded,
        whis=whiskers,
        patch_artist=True
    )
    for patch, color in zip(bp_fwd['boxes'], colors_fwd):
        patch.set_facecolor(color)
    handles_fwd = []
    for color, label in zip(colors_fwd, boxplot_labels):
        handles_fwd.append(mpatches.Patch(color=color, label=label))
    plt.legend(handles=handles_fwd)
    plt.title("Boxplot Pacchetti Forwardati")
    plt.ylabel("Forwarded Count")
    plt.grid(True, linestyle="--", alpha=0.7)
    
    if boxplot_y_limits is not None:
        plt.ylim(boxplot_y_limits)
        
    plt.tight_layout()
    plt.show()

    # --- Boxplot per pacchetti droppati ---
    colors_drp = plt.cm.tab10(np.linspace(0, 1, len(boxplot_data_dropped)))
    plt.figure(figsize=(10, 6))
    bp_drp = plt.boxplot(
        boxplot_data_dropped,
        whis=whiskers,
        patch_artist=True
    )
    for patch, color in zip(bp_drp['boxes'], colors_drp):
        patch.set_facecolor(color)
    handles_drp = []
    for color, label in zip(colors_drp, boxplot_labels):
        handles_drp.append(mpatches.Patch(color=color, label=label))
    plt.legend(handles=handles_drp)
    plt.title("Boxplot Pacchetti Droppati")
    plt.ylabel("Dropped Count")
    plt.grid(True, linestyle="--", alpha=0.7)
    
    if boxplot_y_limits is not None:
        plt.ylim(boxplot_y_limits)
        
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    file_list = [
        "Uniform_B_N500_I05_S1e3.json",
        "Lognormal_B_N500_I05_S1e3.json"
    ]

    SUBSAMPLE_NUMBER = 100
    SUBSAMPLE_RATE = 90
    QUEUE_Y_LIMITS = (0, 60)
    RESPONSE_Y_LIMITS = None  # (0, 600)
    X_LIMIT = (100, 500)

    boxplot_whiskers = None
    # boxplot_whiskers = (5, 95)
    boxplot_y_limits = (0, 80000)

    plot_graph(
        file_list,
        SUBSAMPLE_NUMBER,
        SUBSAMPLE_RATE,
        QUEUE_Y_LIMITS,
        RESPONSE_Y_LIMITS,
        X_LIMIT,
        boxplot_whiskers=boxplot_whiskers,
        boxplot_y_limits=boxplot_y_limits
    )
