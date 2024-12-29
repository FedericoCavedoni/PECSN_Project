import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

def extract_statistics(data, subsample_rate=None, subsample_number=None):
    scalars = defaultdict(list)
    vectors = defaultdict(list)
    for run_name, run_content in data.items():
        for scalar in run_content.get("scalars", []):
            module = scalar.get("module", "")
            name = scalar.get("name", "")
            value = scalar.get("value", 0)
            scalars[module].append((name, value))
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
            vectors[module].append((name, times, values))
    return scalars, vectors

def compute_mean_time_series(vectors, key):
    mean_series = defaultdict(list)
    for module, data in vectors.items():
        for name, times, values in data:
            if key in name:
                all_times = sorted(set(times))
                time_to_values = defaultdict(list)
                for t, v in zip(times, values):
                    time_to_values[t].append(v)
                mean_times = []
                mean_values = []
                for t in all_times:
                    if time_to_values[t]:
                        mean_times.append(t)
                        mean_values.append(np.mean(time_to_values[t]))
                mean_series[module] = (mean_times, mean_values)
    return mean_series

def plot_mean_time_series(mean_series, title, ylabel, theoretical_time, y_limits=None, x_limit=None):
    plt.figure(figsize=(10, 6))
    all_response_values = []
    for module, (times, values) in sorted(mean_series.items(), key=lambda x: x[0]):
        all_response_values.extend(values)
        if x_limit:
            filtered_times = [t for t in times if t <= x_limit]
            filtered_values = [v for t, v in zip(times, values) if t <= x_limit]
        else:
            filtered_times = times
            filtered_values = values
        plt.plot(filtered_times, filtered_values, label=f"{module}")
    practical_mean = np.mean(all_response_values) if all_response_values else 0.0
    plt.axhline(y=theoretical_time, color='black', linestyle='--', label=f"Theoretical Mean = {theoretical_time:.2f}")
    plt.axhline(y=practical_mean, color='blue', linestyle='--', label=f"Practical Mean = {practical_mean:.2f}")
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
    plt.show()

def calculate_service_rate(S, lambda_instruction):
    return S * lambda_instruction

def main(json_path, option, S, lambda_instruction, lambda_interarrival, D, subsample_rate=None, subsample_number=None, queue_y_limits=None, response_y_limits=None, x_limit=None):
    service_rate = calculate_service_rate(S, lambda_instruction)
    lambda_value = lambda_interarrival
    if service_rate <= lambda_value:
        raise ValueError("Service rate must be greater than arrival rate to avoid instability.")
    if option == "A":
        theoretical_time = 1 / (service_rate - lambda_value)
    elif option == "B":
        theoretical_time = D + (1 / (service_rate - lambda_value))
    else:
        raise ValueError(f"Invalid option: {option}. Choose 'A' or 'B'.")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    scalars, vectors = extract_statistics(data, subsample_rate=subsample_rate, subsample_number=subsample_number)
    mean_response_time = compute_mean_time_series(vectors, "responseTime:vector")
    plot_mean_time_series(mean_response_time, "Average Response Time", "Response Time (s)", theoretical_time, y_limits=response_y_limits, x_limit=x_limit)

if __name__ == "__main__":
    file_path = "data/normal_A.json"
    option = file_path.split("_")[1].split(".")[0].upper()
    S = 10
    lambda_instruction = 1/10
    lambda_interarrival = 1/10
    D = 0.1
    subsample_number = None
    subsample_rate = 99.0
    x_limits = 900
    queue_y_limits = (0, 11)
    response_y_limits = (0, 10)
    main(json_path=file_path, option=option, S=S, lambda_instruction=lambda_instruction, lambda_interarrival=lambda_interarrival, D=D, subsample_rate=subsample_rate, subsample_number=subsample_number, queue_y_limits=queue_y_limits, response_y_limits=response_y_limits, x_limit=x_limits)
