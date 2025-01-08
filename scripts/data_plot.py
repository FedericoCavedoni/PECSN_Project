import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
from data_extraction import *

def plot_mean_time_series(mean_series, title, ylabel, y_limits=None, x_limit=None, save_path=None):
    plt.figure(figsize=(10, 6))
    all_values = []
    for module, (_, values) in mean_series.items():
        all_values.extend(values)
    global_mean = np.mean(all_values) if all_values else 0.0
    for module in sorted(mean_series.keys()):
        times, values = mean_series[module]
        if x_limit:
            times, values = zip(*[(t, v) for t, v in zip(times, values) if x_limit[0] <= t <= x_limit[1]])
        plt.plot(times, values, label=module)
    #plt.axhline(global_mean, color='red', linestyle='--', label=f"Global Mean = {global_mean:.2f}")
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    if y_limits:
        plt.ylim(y_limits)
    if x_limit:
        plt.xlim(x_limit)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def plot_boxplot_from_vectors(vectors, key, title, ylabel, convert_to_ms=False, save_path=None):
    plt.figure(figsize=(12, 6))
    data = []
    labels = []
    colors = []
    cmap = plt.cm.get_cmap("tab20")

    for i, (module, metrics) in enumerate(vectors.items()):
        if key in metrics:
            all_values = []
            for _, values in metrics[key]:
                if convert_to_ms:
                    all_values.extend([v * 1000 for v in values])
                else:
                    all_values.extend(values)
            data.append(all_values)
            labels.append(module)
            colors.append(cmap(i % cmap.N))

    if data:
        box = plt.boxplot(data, patch_artist=True)
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)

        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks([])
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        legend_patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
        plt.legend(handles=legend_patches, title="Basestations", loc="upper right", bbox_to_anchor=(1.2, 1))
        plt.tight_layout()
        
        #plt.ylim(0, 800)

        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    else:
        print(f"No data available for key '{key}' to plot.")

def plot_boxplot_from_scalars(scalars, key, title, ylabel, save_path=None):
    plt.figure(figsize=(12, 6))
    data = []
    labels = []
    colors = []
    cmap = plt.cm.get_cmap("tab20")
    for i, (module, metrics) in enumerate(scalars.items()):
        if key in metrics:
            data.append(metrics[key])
            labels.append(module)
            colors.append(cmap(i % cmap.N))
    if data:
        box = plt.boxplot(data, patch_artist=True)
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks([])
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        legend_patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
        plt.legend(handles=legend_patches, title="Basestations", loc="upper right", bbox_to_anchor=(1.2, 1))
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    else:
        print(f"No data available for key '{key}' to plot.")

def plot_boxplots(vectors, scalars, opz):
    # Box Plot per response time (convert_to_ms=True)
    plot_boxplot_from_vectors(
        vectors,
        key="responseTime:vector",
        title="Response Time Distribution by Basestation",
        ylabel="Response Time (ms)",
        convert_to_ms=True
    )

    # Box Plot per queue length (convert_to_ms=False)
    plot_boxplot_from_vectors(
        vectors,
        key="queueLength:vector",
        title="Queue Length Distribution by Basestation",
        ylabel="Queue Length",
        convert_to_ms=False
    )

    # Se l'opzione è "B", stampiamo anche i forwarded
    if opz == "B":
        plot_boxplot_from_scalars(
            scalars,
            key="forwarded:count",
            title="Forwarded Packets Distribution by Basestation",
            ylabel="Number of Forwarded Packets"
        )

    # Box Plot per dropped packets
    plot_boxplot_from_scalars(
        scalars,
        key="dropped:count",
        title="Dropped Packets Distribution by Basestation",
        ylabel="Number of Dropped Packets"
    )

def plot_timeseries(mean_queue_length, mean_response_time, QUEUE_Y_LIMITS=None, RESPONSE_Y_LIMITS=None, X_LIMIT=None):
    plot_mean_time_series(
        mean_queue_length,
        "Average Queue Length",
        "Queue Length",
        y_limits=QUEUE_Y_LIMITS,
        x_limit=X_LIMIT,
    )
    plot_mean_time_series(
        mean_response_time,
        "Average Response Time",
        "Response Time (ms)",
        y_limits=RESPONSE_Y_LIMITS,
        x_limit=X_LIMIT,
    )

def print_vector_statistics(vectors, key, label, convert_to_ms=False):
    print(f"\n=== {label} Statistics ===")
    data = flatten_vector_data(vectors, key, convert_to_ms=convert_to_ms)
    if not data:
        print(f"  Nessun dato disponibile per il vettore '{key}'.")
        return
    for module, values in data.items():
        mean, margin, ci_low, ci_high = compute_average_and_ci(values)
        print(f"{module}: mean = {mean:.2f}, 95% CI = [{ci_low:.2f}, {ci_high:.2f}]")
    print()

def print_scalar_statistics(scalars, key, label):
    print(f"\n=== {label} Statistics ===")
    data = compute_averages_with_ci(scalars, key)
    if not data:
        print(f"  Nessun dato disponibile per lo scalare '{key}'.")
        return
    for module, stats in data.items():
        mean = stats["mean"]
        margin = stats["margin"]
        ci_low = stats["ci_low"]
        ci_high = stats["ci_high"]
        print(f"{module}: mean = {mean:.2f}, 95% CI = [{ci_low:.2f}, {ci_high:.2f}]")
    print()

def print_total_packets(scalars, key, label):
    total = compute_totals(scalars, key)
    print(f"Total {label}: {total}\n")

def print_all_statistics(scalars, vectors):
    print_vector_statistics(vectors, key="responseTime:vector", label="Response Time", convert_to_ms=True)
    print_vector_statistics(vectors, key="queueLength:vector", label="Queue Length", convert_to_ms=False)
    print_scalar_statistics(scalars, key="dropped:count", label="Dropped Packets")
    print_scalar_statistics(scalars, key="forwarded:count", label="Forwarded Packets")
    print_total_packets(scalars, key="dropped:count", label="Dropped Packets")
    print_total_packets(scalars, key="forwarded:count", label="Forwarded Packets")


def plot_aggregated_time_series(vectors, key, title, convert_to_ms=False, y_limits=None, x_limit=None, save_path=None):
    valid_modules = []
    all_times_list = []
    for module, metric_dict in vectors.items():
        if key in metric_dict:
            valid_modules.append(module)
            for times, values in metric_dict[key]:
                all_times_list.extend(times)
                
    if not valid_modules:
        print(f"Nessun dato disponibile per il vettore '{key}'.")
        return

    all_times = np.unique(all_times_list)
    if len(all_times) == 0:
        print(f"Nessun dato disponibile per il vettore '{key}'.")
        return
    
    sum_values = np.zeros_like(all_times, dtype=float)  
    count_values = np.zeros_like(all_times, dtype=float) 

    for module in valid_modules:
        for times, values in vectors[module][key]:
            times = np.array(times, dtype=float)
            values = np.array(values, dtype=float)
            if len(times) > 1:
                interpolated = np.interp(all_times, times, values)
            else:
                interpolated = np.full_like(all_times, values[0] if len(values) > 0 else 0.0)
            
            sum_values += interpolated
            count_values += (interpolated != 0)  

    with np.errstate(divide='ignore', invalid='ignore'):
        mean_values = np.divide(sum_values, count_values, 
                                out=np.zeros_like(sum_values), 
                                where=(count_values!=0))
        
    if convert_to_ms:
        mean_values *= 1000.0

    if x_limit:
        idx = (all_times >= x_limit[0]) & (all_times <= x_limit[1])
        if not np.any(idx):
            print(f"Nessun dato nel range temporale indicato: {x_limit}.")
            return
        all_times = all_times[idx]
        mean_values = mean_values[idx]

    plt.figure(figsize=(10, 6))
    plt.plot(all_times, mean_values, label="Aggregated Mean", color="blue")
    
    global_mean = np.mean(mean_values) if len(mean_values) > 0 else 0.0
    plt.axhline(global_mean, color='red', linestyle='--', label=f"Overall Mean = {global_mean:.2f}")

    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("ms" if convert_to_ms else "Value")

    if y_limits:
        plt.ylim(y_limits)
    if x_limit:
        plt.xlim(x_limit)

    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()


def plot_aggregated_response_time_and_queue_length(vectors, y_limits_resp=None, y_limits_queue=None, x_limit=None):
    plot_aggregated_time_series(
        vectors,
        key="responseTime:vector",
        title="Aggregated Response Time",
        convert_to_ms=True,
        y_limits=y_limits_resp,
        x_limit=x_limit
    )
    plot_aggregated_time_series(
        vectors,
        key="queueLength:vector",
        title="Aggregated Queue Length",
        convert_to_ms=False,
        y_limits=y_limits_queue,
        x_limit=x_limit
    )
