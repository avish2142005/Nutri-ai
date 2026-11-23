"""KrishiNetra Plotting and Visualization Utilities.

Generates:
1. Training and validation loss curves.
2. Training and validation accuracy curves.
3. Confusion matrix heatmap.
4. Per-class F1 score bar chart.
5. Comparative model radar and bar charts (Accuracy vs Latency vs Model Size).
"""

import os
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns


def plot_training_history(history: Dict[str, Any], output_path: str or Path):
    """Plot training vs validation accuracy and loss over epochs."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    train_loss = history.get("train_loss", [])
    val_loss = history.get("val_loss", [])
    train_acc = [a * 100 for a in history.get("train_acc", [])]
    val_acc = [a * 100 for a in history.get("val_acc", [])]
    epochs = range(1, len(train_loss) + 1)
    arch = history.get("architecture", "Model")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Loss plot
    ax1.plot(epochs, train_loss, "b-o", label="Training Loss", linewidth=2)
    ax1.plot(epochs, val_loss, "r--s", label="Validation Loss", linewidth=2)
    ax1.set_title(f"{arch} - Training & Validation Loss", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch", fontsize=11)
    ax1.set_ylabel("CrossEntropy Loss", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right")

    # Accuracy plot
    ax2.plot(epochs, train_acc, "g-o", label="Training Accuracy", linewidth=2)
    ax2.plot(epochs, val_acc, "m--s", label="Validation Accuracy", linewidth=2)
    ax2.set_title(f"{arch} - Training & Validation Accuracy", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch", fontsize=11)
    ax2.set_ylabel("Accuracy (%)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_confusion_matrix(cm: np.ndarray, class_names: List[str], output_path: str or Path, title: str = "Confusion Matrix"):
    """Plot high-resolution normalized confusion matrix."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize rows to percentages
    row_sums = cm.sum(axis=1)[:, np.newaxis]
    row_sums[row_sums == 0] = 1.0
    cm_norm = cm.astype("float") / row_sums

    # For readability if many classes, shorten labels
    clean_labels = [c.replace("___", " ").replace("_", " ") for c in class_names]

    plt.figure(figsize=(16, 14))
    sns.heatmap(
        cm_norm,
        annot=len(class_names) <= 20,
        fmt=".2f",
        cmap="YlGnBu",
        xticklabels=clean_labels,
        yticklabels=clean_labels,
        cbar_kws={"label": "Normalized Ratio"}
    )
    plt.title(title, fontsize=15, fontweight="bold", pad=15)
    plt.xlabel("Predicted Class", fontsize=12, fontweight="bold")
    plt.ylabel("Ground Truth Class", fontsize=12, fontweight="bold")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_model_comparison(comparison_data: List[Dict[str, Any]], output_path: str or Path):
    """Plot multi-attribute comparison chart across EfficientNetB3, ResNet50, MobileNetV2."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    models_names = [d["architecture"] for d in comparison_data]
    accuracies = [d["test_accuracy_pct"] for d in comparison_data]
    latencies = [d["avg_latency_ms"] for d in comparison_data]
    sizes_mb = [d["model_size_mb"] for d in comparison_data]
    f1_scores = [d["macro_f1"] * 100 for d in comparison_data]

    x = np.arange(len(models_names))
    width = 0.2

    fig, ax1 = plt.subplots(figsize=(12, 6))

    rects1 = ax1.bar(x - width*1.5, accuracies, width, label="Test Accuracy (%)", color="#2ca02c")
    rects2 = ax1.bar(x - width*0.5, f1_scores, width, label="Macro F1 (%)", color="#1f77b4")
    rects3 = ax1.bar(x + width*0.5, sizes_mb, width, label="Model Size (MB)", color="#ff7f0e")
    rects4 = ax1.bar(x + width*1.5, latencies, width, label="Inference Latency (ms)", color="#d62728")

    ax1.set_ylabel("Metric Value", fontsize=12, fontweight="bold")
    ax1.set_title("KrishiNetra Architecture Benchmark: EfficientNetB3 vs ResNet50 vs MobileNetV2", fontsize=14, fontweight="bold", pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(models_names, fontsize=12, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax1.annotate(f"{height:.1f}",
                         xy=(rect.get_x() + rect.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha="center", va="bottom", fontsize=9, fontweight="bold")

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    autolabel(rects4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
