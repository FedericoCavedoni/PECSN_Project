import os
import json
import numpy as np
from collections import defaultdict

def load_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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

def compute_average_and_ci(values, confidence=0.95):
    arr = np.array(values, dtype=float)
    n = len(arr)
    if n < 2:
        if n == 1:
            return arr[0], 0.0, arr[0], arr[0]
        else:
            return 0.0, 0.0, 0.0, 0.0

    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    z = 1.96
    margin = z * (std / np.sqrt(n))
    lower_bound = mean - margin
    upper_bound = mean + margin
    return mean, margin, lower_bound, upper_bound

def compute_averages_with_ci(scalars, key):
    results = {}
    for module, metrics in scalars.items():
        if key in metrics:
            values = [v if v is not None else 0 for v in metrics[key]]
            mean, margin, ci_low, ci_high = compute_average_and_ci(values)
            results[module] = {
                "mean": mean,
                "margin": margin,
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
    return results

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
                    m_val = np.mean(time_to_values[t])
                    if convert_to_ms:
                        m_val *= 1000
                    mean_values.append(m_val)
            mean_series[module] = (mean_times, mean_values)
    return mean_series

def compute_totals(scalars, key):
    total = 0
    for module, metrics in scalars.items():
        if key in metrics:
            total += sum([v if v is not None else 0 for v in metrics[key]])
    return total

def flatten_vector_data(vectors_dict, key, convert_to_ms=False):
    data = defaultdict(list)
    for module, metrics in vectors_dict.items():
        if key in metrics:
            for times, values in metrics[key]:
                if convert_to_ms:
                    values = [v * 1000 for v in values]
                data[module].extend(values)
    return data

def parse_filename(filename):
    import os
    base = os.path.basename(filename)
    base = os.path.splitext(base)[0]
    parts = base.split("_")

    distribution = parts[0]
    opzione = parts[1]
    n_users = int(parts[2][1:])

    i_str = parts[3][1:]
    val = float(i_str)
    if len(i_str) == 2:
        interarrival = val / 10.0
    else:
        interarrival = val

    size_str = parts[4][1:]
    try:
        packet_size = float(size_str)
    except ValueError:
        packet_size = size_str

    return {
        "distribution": distribution,
        "opzione": opzione,
        "n_users": n_users,
        "interarrival": interarrival,
        "packet_size": packet_size
    }
