import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from data_extraction import (
    parse_filename,
    load_data,
    extract_statistics,
)
from multi_file_graph import (
    aggregate_mean_time_series
)

def plot_by_parameter(
    file_list,
    SUBSAMPLE_NUMBER,
    SUBSAMPLE_RATE,
    param_name="N",  
    X_LIMIT=None,
    ci_z=1.96
):
    # Dizionario per salvare i risultati raggruppati per valore di param_name
    results = {}

    # --- Lettura e aggregazione dati ---
    for json_file in file_list:
        params = parse_filename(json_file)
        dist = params["distribution"]
        opz = params["opzione"]
        iat = params["interarrival"]
        num_user = params["n_users"]
        size_rate = params["size_rate"]

        # Seleziona la "chiave" in base a param_name
        if param_name == "N":
            varying_param = num_user
        elif param_name == "I":
            varying_param = iat
        elif param_name == "S":
            varying_param = size_rate
        else:
            raise ValueError("param_name non valido. Usa 'N', 'I' o 'S'.")

        file_name = os.path.join("data", json_file)
        data = load_data(file_name)
        scalars, vectors = extract_statistics(
            data,
            subsample_rate=SUBSAMPLE_RATE,
            subsample_number=SUBSAMPLE_NUMBER
        )

        # Otteniamo i vettori medi nel tempo
        rt_times, rt_values = aggregate_mean_time_series(
            vectors, "responseTime:vector", convert_to_ms=True
        )
        ql_times, ql_values = aggregate_mean_time_series(
            vectors, "queueLength:vector", convert_to_ms=False
        )

        # Limitazione asse X se servono
        if X_LIMIT is not None:
            (t_min, t_max) = X_LIMIT

            rt_idx = (rt_times >= t_min) & (rt_times <= t_max)
            rt_times = rt_times[rt_idx]
            rt_values = rt_values[rt_idx]

            ql_idx = (ql_times >= t_min) & (ql_times <= t_max)
            ql_times = ql_times[ql_idx]
            ql_values = ql_values[ql_idx]

        # Salviamo nel dizionario
        results[varying_param] = {
            "dist": dist,
            "opz": opz,
            "rt_times": rt_times,
            "rt_values": rt_values,
            "ql_times": ql_times,
            "ql_values": ql_values
        }

    # Ordiniamo i parametri (chiavi) in senso crescente
    sorted_keys = sorted(results.keys(), key=lambda x: float(x))

    # Liste per creare i grafici
    param_values = []
    rt_means = []
    rt_cis = []     # half-width dell'IC
    ql_means = []
    ql_cis = []     # half-width dell'IC

    # --- Calcolo statistiche e CI ---
    for k in sorted_keys:
        rt_vals = results[k]["rt_values"]
        ql_vals = results[k]["ql_values"]

        n_rt = len(rt_vals)
        n_ql = len(ql_vals)

        # Media e Standard Error per RT
        if n_rt > 0:
            mean_rt = np.mean(rt_vals)
            std_rt = np.std(rt_vals, ddof=1)  # ddof=1 per stima unbiased
            se_rt = std_rt / np.sqrt(n_rt)
            ci_rt = ci_z * se_rt
        else:
            mean_rt = 0
            ci_rt = 0

        # Media e Standard Error per QL
        if n_ql > 0:
            mean_ql = np.mean(ql_vals)
            std_ql = np.std(ql_vals, ddof=1)
            se_ql = std_ql / np.sqrt(n_ql)
            ci_ql = ci_z * se_ql
        else:
            mean_ql = 0
            ci_ql = 0

        param_values.append(k)
        rt_means.append(mean_rt)
        rt_cis.append(ci_rt)
        ql_means.append(mean_ql)
        ql_cis.append(ci_ql)

    # ==================== PLOT FINALE ====================
    # 1) Plot RT con intervallo di confidenza
    plt.figure(figsize=(8, 5))
    plt.errorbar(
        param_values,        # asse X
        rt_means,           # media di RT
        yerr=rt_cis,        # half-width intervallo
        fmt='o-',           # marker e linea
        capsize=5,          # "cappucci" degli error bar
        label=f"Mean Response Time"
    )
    plt.xlabel(f"{param_name} value")
    plt.ylabel("Response Time (ms)")
    plt.title(f"Mean Response Time vs. {param_name}")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # 2) Plot QL con intervallo di confidenza
    plt.figure(figsize=(8, 5))
    plt.errorbar(
        param_values,
        ql_means,
        yerr=ql_cis,
        fmt='o-',
        capsize=5,
        color='orange',
        label=f"Mean Queue Length"
    )
    plt.xlabel(f"{param_name} value")
    plt.ylabel("Queue Length")
    plt.title(f"Mean Queue Length vs. {param_name}")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Esempio di file list
    file_list = [
        "Uniform_A_N250_I05_S1e2.json",
        "Uniform_A_N250_I05_S1e3.json",
        "Uniform_A_N250_I05_S1e4.json"
    ]

    # Parametri 
    SUBSAMPLE_NUMBER = 100
    SUBSAMPLE_RATE = 90
    
    X_LIMIT = None  # Oppure (0, 500)

    # Parametro che varia: "N", "I", o "S"
    param_name = "S"

    # Valore di z per l'intervallo di confidenza (default ~95%)
    ci_z = 1.96  # ~95%; 1.645 ~90%, 2.576 ~99%, etc.

    plot_by_parameter(
        file_list=file_list,
        SUBSAMPLE_NUMBER=SUBSAMPLE_NUMBER,
        SUBSAMPLE_RATE=SUBSAMPLE_RATE,
        param_name=param_name,
        X_LIMIT=X_LIMIT,
        ci_z=ci_z
    )
