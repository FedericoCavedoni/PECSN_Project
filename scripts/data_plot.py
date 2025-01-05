import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def plot_mean_time_series_with_ci(mean_series, ci_series, title, ylabel, y_limits=None, x_limit=None, save_path=None):
    plt.figure(figsize=(10, 6))
    all_values = []
    for module, (_, values) in mean_series.items():
        all_values.extend(values)
    global_mean = np.mean(all_values) if all_values else 0.0

    for module in sorted(mean_series.keys()):
        times, values = mean_series[module]
        lower_ci, upper_ci = ci_series.get(module, ([], []))
        if x_limit:
            times, values = zip(*[(t, v) for t, v in zip(times, values) if x_limit[0] <= t <= x_limit[1]])
            lower_ci = lower_ci[:len(times)]
            upper_ci = upper_ci[:len(times)]
        plt.plot(times, values, label=module)
        if lower_ci and upper_ci:
            plt.fill_between(times, lower_ci, upper_ci, alpha=0.2, label=f"{module} CI")

    plt.axhline(global_mean, color='red', linestyle='--', label=f"Global Mean = {global_mean:.2f}")
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


def plot_boxplot_from_vectors(vectors, key, title, ylabel, save_path=None):
    plt.figure(figsize=(12, 6))
    data = []
    labels = []
    colors = []

    # Creazione dei dati e dei colori per le basestation
    cmap = plt.cm.get_cmap("tab20")  # Usa una colormap con molti colori
    for i, (module, metrics) in enumerate(vectors.items()):
        if key in metrics:
            all_values = []
            for _, values in metrics[key]:
                all_values.extend([v * 1000 for v in values])  # Conversione in ms
            data.append(all_values)
            labels.append(module)
            colors.append(cmap(i % cmap.N))  # Cicla sui colori della colormap

    if data:
        # Creazione del box plot con colori personalizzati
        box = plt.boxplot(data, patch_artist=True)

        # Applica i colori alle box
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)

        # Configura il grafico
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks([])  # Rimuove i nomi dal sotto delle box
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        # Creazione della legenda
        legend_patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
        plt.legend(handles=legend_patches, title="Basestations", loc="upper right", bbox_to_anchor=(1.2, 1))

        # Layout e salvataggio/mostra
        plt.tight_layout()
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

    # Creazione dei dati e dei colori per le basestation
    cmap = plt.cm.get_cmap("tab20")
    for i, (module, metrics) in enumerate(scalars.items()):
        if key in metrics:
            data.append(metrics[key])
            labels.append(module)
            colors.append(cmap(i % cmap.N))  # Cicla sui colori della colormap

    if data:
        # Creazione del box plot con colori personalizzati
        box = plt.boxplot(data, patch_artist=True)

        # Applica i colori alle box
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)

        # Configura il grafico
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks([])  # Rimuove i nomi dal sotto delle box
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        # Creazione della legenda
        legend_patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
        plt.legend(handles=legend_patches, title="Basestations", loc="upper right", bbox_to_anchor=(1.2, 1))

        # Layout e salvataggio/mostra
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    else:
        print(f"No data available for key '{key}' to plot.")


