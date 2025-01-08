from data_extraction import *
from data_plot import *

def plot_graph(file_name, SUBSAMPLE_NUMBER, SUBSAMPLE_RATE, QUEUE_Y_LIMITS, RESPONSE_Y_LIMITS, X_LIMIT):
    JSON_INPUT_FILE = f"data/{file_name}.json"
    
    params = parse_filename(JSON_INPUT_FILE)
    opz = params["opzione"] 

    # Caricamento e preparazione dati
    data = load_data(JSON_INPUT_FILE)
    scalars, vectors = extract_statistics(data, SUBSAMPLE_RATE, SUBSAMPLE_NUMBER)
    
    # Stampa di TUTTE le statistiche richieste
    print_all_statistics(scalars, vectors)

    # Calcolo statistiche (medie temporali) per i plot
    mean_queue_length = compute_mean_time_series(vectors, "queueLength:vector")
    mean_response_time = compute_mean_time_series(vectors, "responseTime:vector", convert_to_ms=True)

    # Plot dei grafici di time series
    plot_timeseries(mean_queue_length, mean_response_time,QUEUE_Y_LIMITS=QUEUE_Y_LIMITS,RESPONSE_Y_LIMITS=RESPONSE_Y_LIMITS,X_LIMIT=X_LIMIT)

    # Plot dei boxplot
    plot_boxplots(vectors, scalars, opz)
    
    # Plot delle timeseries aggregate
    # plot_aggregated_response_time_and_queue_length(vectors,y_limits_queue=QUEUE_Y_LIMITS,y_limits_resp=RESPONSE_Y_LIMITS,x_limit=X_LIMIT)

if __name__ == "__main__":
    file_name = "Lognormal_A_N250_I05_S1e3"
    
    SUBSAMPLE_NUMBER = 100
    SUBSAMPLE_RATE = 90
    
    QUEUE_Y_LIMITS = None #(0,60)
    RESPONSE_Y_LIMITS = None #(0,100)
    X_LIMIT = None #(0, 500)
    
    plot_graph(file_name, SUBSAMPLE_NUMBER, SUBSAMPLE_RATE, QUEUE_Y_LIMITS, RESPONSE_Y_LIMITS, X_LIMIT)