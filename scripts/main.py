from data_extraction import *
from data_plot import *


if __name__ == "__main__":
    file_name = "Lognormal_A_N250_I05_S1e3"
    JSON_INPUT_FILE = f"data/{file_name}.json"
    SUBSAMPLE_NUMBER = 100
    SUBSAMPLE_RATE = 90
    QUEUE_Y_LIMITS = None
    RESPONSE_Y_LIMITS = None
    X_LIMIT = None

    # Caricamento e preparazione dati
    data = load_data(JSON_INPUT_FILE)
    scalars, vectors = extract_statistics(data, SUBSAMPLE_RATE, SUBSAMPLE_NUMBER)

    # Calcolo statistiche
    mean_queue_length = compute_mean_time_series(vectors, "queueLength:vector")
    mean_response_time = compute_mean_time_series(vectors, "responseTime:vector", convert_to_ms=True)

    # Plot delle medie temporali con CI
    plot_mean_time_series_with_ci(
        mean_queue_length,
        {},
        "Average Queue Length with CI",
        "Queue Length",
        y_limits=QUEUE_Y_LIMITS,
        x_limit=X_LIMIT,
    )

    plot_mean_time_series_with_ci(
        mean_response_time,
        {},
        "Average Response Time with CI",
        "Response Time (ms)",
        y_limits=RESPONSE_Y_LIMITS,
        x_limit=X_LIMIT,
    )

    # Box Plot per response time
    plot_boxplot_from_vectors(
        vectors,
        "responseTime:vector",
        "Response Time Distribution by Basestation",
        "Response Time (ms)"
    )

    # Box Plot per forwarded packets
    plot_boxplot_from_scalars(
        scalars,
        "forwarded:count",
        "Forwarded Packets Distribution by Basestation",
        "Number of Forwarded Packets"
    )

    # Box Plot per dropped packets
    plot_boxplot_from_scalars(
        scalars,
        "dropped:count",
        "Dropped Packets Distribution by Basestation",
        "Number of Dropped Packets"
    )
