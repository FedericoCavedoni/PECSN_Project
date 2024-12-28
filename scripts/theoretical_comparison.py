import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

def compute_averages(data):
    return {
        bs_id: np.mean([v for v in values if v is not None]) if values else 0.0
        for bs_id, values in data.items()
    }

def aggregate_time_series(data):
    queue_length_series = defaultdict(list)
    response_time_series = defaultdict(list)
    for run_name, run_content in data.items():
        vectors = run_content.get("vectors", [])
        for vector in vectors:
            module = vector.get("module", "")
            name = vector.get("name", "")
            times = vector.get("time", [])
            values = vector.get("value", [])
            bs_id = module.split("[")[-1].rstrip("]") if "baseStations" in module else None
            if not bs_id:
                continue
            if "queueLength:vector" in name:
                queue_length_series[bs_id].append((times, values))
            elif "responseTime:vector" in name:
                response_time_series[bs_id].append((times, values))
    return queue_length_series, response_time_series

def compute_mean_time_series(data, subsample_rate=None):
    mean_series = {}
    for bs_id, series_list in data.items():
        all_times = set()
        for times, _ in series_list:
            all_times.update(times)
        all_times = sorted(all_times)
        time_to_values = {t: [] for t in all_times}
        for times, values in series_list:
            times_arr = np.array(times)
            values_arr = np.array(values)
            for t in all_times:
                if t >= times_arr[0] and t <= times_arr[-1]:
                    idx = np.argmin(np.abs(times_arr - t))
                    time_to_values[t].append(values_arr[idx])
        mean_times = []
        mean_values = []
        for t in all_times:
            if time_to_values[t]:
                mean_times.append(t)
                mean_values.append(np.mean(time_to_values[t]))
        if subsample_rate and len(mean_times) > subsample_rate:
            indices = np.linspace(0, len(mean_times) - 1, subsample_rate, dtype=int)
            mean_times = [mean_times[i] for i in indices]
            mean_values = [mean_values[i] for i in indices]
        mean_series[bs_id] = (mean_times, mean_values)
    return mean_series

def plot_mean_time_series(mean_series, title, ylabel, theoretical_time, y_limits=None, x_limit=None):
    plt.figure(figsize=(10, 6))
    all_response_values = []
    for bs_id in sorted(mean_series.keys(), key=lambda x: int(x)):
        times, values = mean_series[bs_id]
        all_response_values.extend(values)
        if x_limit:
            filtered_times = [t for t in times if t <= x_limit]
            filtered_values = [v for t, v in zip(times, values) if t <= x_limit]
        else:
            filtered_times = times
            filtered_values = values
        plt.plot(filtered_times, filtered_values, label=f"Basestation {bs_id}")
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

def main(json_path, option, S, lambda_instruction, lambda_interarrival, D, subsample_rate=100, queue_y_limits=None, response_y_limits=None, x_limit=None):
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
    queue_length_series, response_time_series = aggregate_time_series(data)
    mean_response_time = compute_mean_time_series(response_time_series, subsample_rate=subsample_rate)
    plot_mean_time_series(mean_response_time, "Average Response Time", "Response Time (s)", theoretical_time, y_limits=response_y_limits, x_limit=x_limit)

if __name__ == "__main__":
    file_path = "data/normal_A.json"
    option = file_path.split("_")[1].split(".")[0].upper()
    
    S = 10
    lambda_instruction = 1/10
    lambda_interarrival = 1/10
    D = 0.1
    
    subsample_rate = None 
    x_limits = 900
    queue_y_limits = (0, 11)
    response_y_limits = (0, 10)
    
    main(json_path=file_path, option=option, S=S, lambda_instruction=lambda_instruction, lambda_interarrival=lambda_interarrival, D=D, subsample_rate=subsample_rate, queue_y_limits=queue_y_limits, response_y_limits=response_y_limits, x_limit=x_limits)
