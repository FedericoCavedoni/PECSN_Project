import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

def load_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_statistics(data):
    scalars = defaultdict(lambda: defaultdict(list))
    vectors = defaultdict(lambda: defaultdict(list))

    for run_name, run_content in data.items():
        for scalar in run_content.get("scalars", []):
            module = scalar.get("module", "")
            name = scalar.get("name", "")
            value = scalar.get("value", 0)
            scalars[module][name].append(value)

        for vector in run_content.get("vectors", []):
            module = vector.get("module", "")
            name = vector.get("name", "")
            times = vector.get("time", [])
            values = vector.get("value", [])
            vectors[module][name].append((times, values))

    return scalars, vectors

def compute_averages(scalars, key):
    averages = {}
    for module, metrics in scalars.items():
        if key in metrics:
            valid_values = [v for v in metrics[key] if v is not None]
            if valid_values:
                averages[module] = np.mean(valid_values)
            else:
                averages[module] = None  
    return averages


def compute_mean_time_series(vectors, key, subsample_rate=None):
    mean_series = {}

    for module, metrics in vectors.items():
        if key in metrics:
            series_list = metrics[key]

            # Combine all time points
            all_times = np.unique(np.concatenate([np.array(times) for times, _ in series_list]))
            time_to_values = {t: [] for t in all_times}

            # Interpolate values
            for times, values in series_list:
                interp_values = np.interp(all_times, times, values)
                for t, v in zip(all_times, interp_values):
                    time_to_values[t].append(v)

            # Compute mean values
            mean_times = []
            mean_values = []
            for t in all_times:
                if time_to_values[t]:
                    mean_times.append(t)
                    mean_values.append(np.mean(time_to_values[t]))

            # Subsample if needed
            if subsample_rate and len(mean_times) > subsample_rate:
                indices = np.linspace(0, len(mean_times) - 1, subsample_rate, dtype=int)
                mean_times = [mean_times[i] for i in indices]
                mean_values = [mean_values[i] for i in indices]

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
        if x_limit:
            times = [t for t in times if t <= x_limit]
            values = values[:len(times)]

        plt.plot(times, values, label=module)

    plt.axhline(y=global_mean, color='red', linestyle='--', label=f"Global Mean = {global_mean:.2f}")

    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    if y_limits:
        plt.ylim(y_limits)
    if x_limit:
        plt.xlim(0, x_limit)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def main(json_path, subsample_rate=None, queue_y_limits=None, response_y_limits=None, x_limit=None):
    data = load_data(json_path)
    scalars, vectors = extract_statistics(data)

    avg_dropped = compute_averages(scalars, "dropped:count")
    avg_forwarded = compute_averages(scalars, "forwarded:count")
    avg_queue = compute_averages(scalars, "queueLength:mean")
    avg_response = compute_averages(scalars, "responseTime:mean")

    print("=== Average Dropped Packets per Basestation ===")
    for module, avg in avg_dropped.items():
        print(f"{module}: {avg:.2f}")

    print("\n=== Average Forwarded Packets per Basestation ===")
    for module, avg in avg_forwarded.items():
        print(f"{module}: {avg:.2f}")

    print("\n=== Average Queue Length per Basestation ===")
    for module, avg in avg_queue.items():
        print(f"{module}: {avg:.2f}")

    print("\n=== Average Response Time per Basestation ===")
    for module, avg in avg_response.items():
        print(f"{module}: {avg:.2f}")

    mean_queue_length = compute_mean_time_series(vectors, "queueLength:vector", subsample_rate=subsample_rate)
    mean_response_time = compute_mean_time_series(vectors, "responseTime:vector", subsample_rate=subsample_rate)

    #plot_mean_time_series(mean_queue_length, "Average Queue Length", "Queue Length", y_limits=queue_y_limits, x_limit=x_limit)
    plot_mean_time_series(mean_response_time, "Average Response Time", "Response Time (ms)", y_limits=response_y_limits, x_limit=x_limit)

if __name__ == "__main__":
    JSON_INPUT_FILE = "data/normal_A.json"
    SUBSAMPLE_RATE = None # 100  # Reduce the number of points processed and displayed

    QUEUE_Y_LIMITS = (0, 20)#None  # None for auto-scaling
    RESPONSE_Y_LIMITS = (0, 20)#None  # None for auto-scaling
    X_LIMIT = 900  # Show data up to time 900

    main(JSON_INPUT_FILE, subsample_rate=SUBSAMPLE_RATE, queue_y_limits=QUEUE_Y_LIMITS, response_y_limits=RESPONSE_Y_LIMITS, x_limit=X_LIMIT)
