import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

def load_data(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing del file JSON: {e}")
        raise

def extract_statistics(data, subsample_rate=None, subsample_number=None):
    scalars = defaultdict(lambda: defaultdict(list))
    vectors = defaultdict(lambda: defaultdict(list))

    for run_name, run_content in data.items():
        for scalar in run_content.get("scalars", []):
            module = scalar.get("module", "")
            name = scalar.get("name", "")
            value = scalar.get("value", 0) if scalar.get("value") is not None else 0  
            scalars[module][name].append(value)

        for vector in run_content.get("vectors", []):
            module = vector.get("module", "")
            name = vector.get("name", "")
            times = vector.get("time", [])
            values = vector.get("value", [])

            if subsample_number is not None:
                n_total = len(times)
                n_keep = min(subsample_number, n_total)
                if n_keep > 1:
                    indices = np.linspace(0, n_total - 1, n_keep, dtype=int)
                    times = [times[i] for i in indices]
                    values = [values[i] for i in indices]
            elif subsample_rate is not None and subsample_rate > 0:
                n_total = len(times)
                discard_fraction = min(subsample_rate / 100.0, 1.0)
                keep_fraction = 1.0 - discard_fraction
                n_keep = int(max(1, np.floor(n_total * keep_fraction)))
                indices = np.linspace(0, n_total - 1, n_keep, dtype=int)
                times = [times[i] for i in indices]
                values = [values[i] for i in indices]

            vectors[module][name].append((times, values))

    return scalars, vectors

def compute_averages(scalars, key):
    averages = {}
    for module, metrics in scalars.items():
        if key in metrics:
            valid_values = [v if v is not None else 0 for v in metrics[key]]  
            averages[module] = np.mean(valid_values) if valid_values else 0
    return averages

def compute_totals(scalars, key):
    total = 0
    for module, metrics in scalars.items():
        if key in metrics:
            total += sum([v if v is not None else 0 for v in metrics[key]])
    return total

def compute_mean_time_series(vectors, key, convert_to_ms=False):
    mean_series = {}
    for module, metrics in vectors.items():
        if key in metrics:
            series_list = metrics[key]
            all_times = np.unique(np.concatenate([np.array(times) for times, _ in series_list]))
            time_to_values = {t: [] for t in all_times}
            for times, values in series_list:
                interp_values = np.interp(all_times, times, values)
                for t, v in zip(all_times, interp_values):
                    time_to_values[t].append(v)
            mean_times = []
            mean_values = []
            for t in all_times:
                if time_to_values[t]:
                    mean_times.append(t)
                    mean_value = np.mean(time_to_values[t])
                    if convert_to_ms:
                        mean_value *= 1000  # Convert value to milliseconds
                    mean_values.append(mean_value)
            mean_series[module] = (mean_times, mean_values)
    return mean_series

def plot_mean_time_series(mean_series, title, ylabel, y_limits=None, x_limit=None, save_path=None):
    plt.figure(figsize=(10, 6))
    all_values = []
    for module, (_, values) in mean_series.items():
        all_values.extend(values)
    global_mean = np.mean(all_values) if all_values else 0.0

    for module in sorted(mean_series.keys()):
        times, values = mean_series[module]
        if x_limit is not None:
            if isinstance(x_limit, tuple) and len(x_limit) == 2:
                x_min, x_max = x_limit
            else:
                x_min, x_max = 0, x_limit
            filtered_times = []
            filtered_values = []
            for t, v in zip(times, values):
                if x_min <= t <= x_max:
                    filtered_times.append(t)
                    filtered_values.append(v)
            times, values = filtered_times, filtered_values
        plt.plot(times, values, label=module)

    plt.axhline(y=global_mean, color='red', linestyle='--', label=f"Global Mean = {global_mean:.2f}")
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    if y_limits:
        plt.ylim(y_limits)
    if x_limit is not None:
        if isinstance(x_limit, tuple) and len(x_limit) == 2:
            plt.xlim(x_limit[0], x_limit[1])
        else:
            plt.xlim(0, x_limit)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def compute_global_mean_time_series(mean_series):
    modules = list(mean_series.keys())
    if not modules:
        return [], []
    all_times = sorted(set(t for (times, _) in mean_series.values() for t in times))
    n_times = len(all_times)
    all_module_values = np.zeros((len(modules), n_times))
    for i, module in enumerate(modules):
        times, values = mean_series[module]
        if len(times) > 1:
            interp_vals = np.interp(all_times, times, values)
        elif len(times) == 1:
            interp_vals = np.array([values[0]] * n_times)
        else:
            interp_vals = np.zeros(n_times)
        all_module_values[i, :] = interp_vals
    global_values = np.mean(all_module_values, axis=0)
    return all_times, global_values

def plot_global_mean_time_series(mean_series, title, ylabel, y_limits=None, x_limit=None, save_path=None):
    plt.figure(figsize=(10, 6))
    all_times, global_values = compute_global_mean_time_series(mean_series)
    if not len(all_times):
        print("Nessun dato disponibile per il plot globale.")
        return
    global_mean = np.mean(global_values)
    if x_limit is not None:
        if isinstance(x_limit, tuple) and len(x_limit) == 2:
            x_min, x_max = x_limit
        else:
            x_min, x_max = 0, x_limit
        filtered_times = []
        filtered_values = []
        for t, v in zip(all_times, global_values):
            if x_min <= t <= x_max:
                filtered_times.append(t)
                filtered_values.append(v)
        all_times, global_values = filtered_times, filtered_values

    plt.plot(all_times, global_values, label="Global Average", color='blue')
    plt.axhline(y=global_mean, color='red', linestyle='--', label=f"Global Mean = {global_mean:.2f}")
    plt.title(title + " (Global Average)")
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    if y_limits:
        plt.ylim(y_limits)
    if x_limit is not None:
        if isinstance(x_limit, tuple) and len(x_limit) == 2:
            plt.xlim(x_limit[0], x_limit[1])
        else:
            plt.xlim(0, x_limit)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def load_and_prepare_data(json_path, subsample_rate=None, subsample_number=None):
    data = load_data(json_path)
    scalars, vectors = extract_statistics(data, subsample_rate, subsample_number)

    avg_dropped = compute_averages(scalars, "dropped:count")
    avg_forwarded = compute_averages(scalars, "forwarded:count")
    avg_queue = compute_averages(scalars, "queueLength:timeavg")
    avg_response = compute_averages(scalars, "responseTime:mean")

    total_dropped = compute_totals(scalars, "dropped:count")
    total_forwarded = compute_totals(scalars, "forwarded:count")

    print("=== Average Dropped Packets per Basestation (SCALAR) ===")
    for module, avg in avg_dropped.items():
        print(f"{module}: {avg:.2f}")

    print(f"\nTotal Dropped Packets: {total_dropped}")

    print("\n=== Average Forwarded Packets per Basestation (SCALAR) ===")
    for module, avg in avg_forwarded.items():
        print(f"{module}: {avg:.2f}")

    print(f"\nTotal Forwarded Packets: {total_forwarded}")

    print("\n=== Average Queue Length per Basestation (SCALAR) ===")
    for module, avg in avg_queue.items():
        print(f"{module}: {avg:.2f}")

    print("\n=== Average Response Time per Basestation (SCALAR) ===")
    for module, avg in avg_response.items():
        print(f"{module}: {avg:.2f}")

    mean_queue_length = compute_mean_time_series(vectors, "queueLength:vector")
    mean_response_time = compute_mean_time_series(vectors, "responseTime:vector", convert_to_ms=True)

    return mean_queue_length, mean_response_time

def plot_each_basestation(mean_queue_length, mean_response_time, queue_y_limits=None, response_y_limits=None, x_limit=None):
    plot_mean_time_series(
        mean_queue_length,
        "Average Queue Length",
        "Queue Length",
        y_limits=queue_y_limits,
        x_limit=x_limit
    )
    plot_mean_time_series(
        mean_response_time,
        "Average Response Time",
        "Response Time (ms)",
        y_limits=response_y_limits,
        x_limit=x_limit
    )

def plot_global_average(mean_queue_length, mean_response_time, queue_y_limits=None, response_y_limits=None, x_limit=None):
    plot_global_mean_time_series(
        mean_queue_length,
        "Average Queue Length",
        "Queue Length",
        y_limits=queue_y_limits,
        x_limit=x_limit
    )
    plot_global_mean_time_series(
        mean_response_time,
        "Average Response Time",
        "Response Time (ms)",
        y_limits=response_y_limits,
        x_limit=x_limit
    )

if __name__ == "__main__":
    file_name = "Lognormal_B_N250_I05_S1e3"
    JSON_INPUT_FILE = f"data/{file_name}.json"

    SUBSAMPLE_NUMBER = 100
    SUBSAMPLE_RATE = 90

    QUEUE_Y_LIMITS = None
    RESPONSE_Y_LIMITS = None
    X_LIMIT = None

    mean_queue_length, mean_response_time = load_and_prepare_data(
        JSON_INPUT_FILE,
        subsample_rate=SUBSAMPLE_RATE,
        subsample_number=SUBSAMPLE_NUMBER
    )

    plot_each_basestation(
        mean_queue_length,
        mean_response_time,
        queue_y_limits=QUEUE_Y_LIMITS,
        response_y_limits=RESPONSE_Y_LIMITS,
        x_limit=X_LIMIT
    )

    """
    plot_global_average(
        mean_queue_length,
        mean_response_time,
        queue_y_limits=QUEUE_Y_LIMITS,
        response_y_limits=RESPONSE_Y_LIMITS,
        x_limit=X_LIMIT
    )
    """