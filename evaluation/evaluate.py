"""KrishiNetra Independent Model Evaluation Engine.

Evaluates trained models on an isolated test dataset split with zero data leakage.
Computes:
- Top-1 and Top-3 Accuracy
- Macro and Weighted Precision, Recall, and F1-score
- Full Confusion Matrix
- Per-class Performance Table
- Inference Latency (ms/sample)
- Model Size (MB) and Parameter Count
- Generates high-res visual plots and structured Markdown/JSON reports.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from dataset.dataset_loader import create_dataloaders
from training.utils import get_device
from training.train_efficientnet import build_efficientnet_b3
from training.train_resnet import build_resnet50
from training.train_mobilenet import build_mobilenet_v2
from evaluation.plot_utils import plot_confusion_matrix, plot_training_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("KrishiNetra.Evaluate")


def load_model(arch: str, weights_path: Path, num_classes: int, device: torch.device) -> nn.Module:
    """Instantiate architecture and load checkpoint weights."""
    if arch == "efficientnet_b3":
        model = build_efficientnet_b3(num_classes=num_classes, freeze_backbone=False)
    elif arch == "resnet50":
        model = build_resnet50(num_classes=num_classes, fine_tune_layer4=False)
    elif arch == "mobilenet_v2":
        model = build_mobilenet_v2(num_classes=num_classes, fine_tune_last_blocks=False)
    else:
        raise ValueError(f"Unknown architecture: {arch}")

    if weights_path.exists():
        checkpoint = torch.load(weights_path, map_location=device)
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
        logger.info(f"Loaded weights from {weights_path}")
    else:
        logger.warning(f"Weights file {weights_path} not found. Using initialized weights for benchmark.")

    model.to(device)
    model.eval()
    return model


def count_parameters(model: nn.Module) -> Tuple[int, int]:
    """Count total and trainable parameters."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total_params, trainable_params


def evaluate_model(
    arch: str = "efficientnet_b3",
    data_dir: str = "dataset/data",
    weights_path: str = None,
    output_dir: str = "models/reports",
    batch_size: int = 16
) -> Dict[str, Any]:
    """Execute independent evaluation on the test dataset split."""
    device = get_device()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if weights_path is None:
        weights_path = Path(f"models/weights/{arch}.pth")
    else:
        weights_path = Path(weights_path)

    # 1. Load Data
    _, _, test_loader, class_names, _ = create_dataloaders(
        data_dir=data_dir,
        arch=arch,
        batch_size=batch_size,
        balance_classes=False
    )
    num_classes = len(class_names)

    # 2. Load Model
    model = load_model(arch, weights_path, num_classes, device)
    total_params, trainable_params = count_parameters(model)
    
    # Model size in MB
    model_size_mb = 0.0
    if weights_path.exists():
        model_size_mb = round(weights_path.stat().st_size / (1024 * 1024), 2)
    else:
        # Approximate size from parameter count
        model_size_mb = round((total_params * 4) / (1024 * 1024), 2)

    # 3. Inference on Test Set
    all_preds = []
    all_targets = []
    all_top3_hits = []
    latencies = []

    logger.info(f"Running evaluation on {len(test_loader.dataset)} independent test images for {arch}...")
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            # Measure inference latency per batch
            t0 = time.perf_counter()
            outputs = model(inputs)
            if device.type == "cuda":
                torch.cuda.synchronize()
            t1 = time.perf_counter()
            batch_latency = (t1 - t0) * 1000.0 / inputs.size(0)  # ms per sample
            latencies.extend([batch_latency] * inputs.size(0))

            probs = torch.softmax(outputs, dim=1)
            _, top1_pred = torch.max(probs, dim=1)
            _, top3_pred = torch.topk(probs, k=min(3, num_classes), dim=1)

            all_preds.extend(top1_pred.cpu().numpy().tolist())
            all_targets.extend(labels.cpu().numpy().tolist())

            for target, top3 in zip(labels.cpu().numpy(), top3_pred.cpu().numpy()):
                all_top3_hits.append(int(target in top3))

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # 4. Compute Metrics
    acc = accuracy_score(all_targets, all_preds)
    top3_acc = float(np.mean(all_top3_hits))
    macro_prec = precision_score(all_targets, all_preds, average="macro", zero_division=0)
    weighted_prec = precision_score(all_targets, all_preds, average="weighted", zero_division=0)
    macro_rec = recall_score(all_targets, all_preds, average="macro", zero_division=0)
    weighted_rec = recall_score(all_targets, all_preds, average="weighted", zero_division=0)
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)
    cm = confusion_matrix(all_targets, all_preds)

    avg_latency = float(np.mean(latencies))

    # Per-class metrics
    report_dict = classification_report(
        all_targets,
        all_preds,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    results = {
        "architecture": arch,
        "test_samples": len(all_targets),
        "total_classes": num_classes,
        "test_accuracy_pct": round(acc * 100, 2),
        "top3_accuracy_pct": round(top3_acc * 100, 2),
        "macro_precision": round(macro_prec, 4),
        "weighted_precision": round(weighted_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "weighted_recall": round(weighted_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "model_size_mb": model_size_mb,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "per_class_report": report_dict
    }

    # Save Confusion Matrix Plot
    cm_plot_path = out_dir / f"{arch}_confusion_matrix.png"
    plot_confusion_matrix(cm, class_names, cm_plot_path, title=f"KrishiNetra {arch} Test Confusion Matrix")
    results["confusion_matrix_plot"] = str(cm_plot_path)

    # Plot Training History if exists
    history_file = out_dir / f"{arch}_history.json"
    if history_file.exists():
        with open(history_file, "r") as f:
            hist = json.load(f)
        hist_plot_path = out_dir / f"{arch}_training_curves.png"
        plot_training_history(hist, hist_plot_path)
        results["training_curves_plot"] = str(hist_plot_path)

    # Save JSON Report
    json_path = out_dir / f"{arch}_evaluation_report.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Generate Markdown Summary
    md_path = out_dir / f"{arch}_evaluation_report.md"
    with open(md_path, "w") as f:
        f.write(f"# KrishiNetra Model Evaluation Report: {arch}\n\n")
        f.write(f"- **Test Accuracy (Top-1)**: {results['test_accuracy_pct']}%\n")
        f.write(f"- **Top-3 Accuracy**: {results['top3_accuracy_pct']}%\n")
        f.write(f"- **Macro F1-Score**: {results['macro_f1']}\n")
        f.write(f"- **Weighted F1-Score**: {results['weighted_f1']}\n")
        f.write(f"- **Average Inference Latency**: {results['avg_latency_ms']} ms/sample\n")
        f.write(f"- **Model Size**: {results['model_size_mb']} MB\n")
        f.write(f"- **Total Parameters**: {results['total_parameters']:,}\n\n")
        f.write("## Per-Class Performance Summary\n\n")
        f.write("| Class Name | Precision | Recall | F1-Score | Support |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for cls in class_names:
            if cls in report_dict:
                c_data = report_dict[cls]
                f.write(f"| `{cls}` | {c_data['precision']:.3f} | {c_data['recall']:.3f} | {c_data['f1-score']:.3f} | {c_data['support']} |\n")

    logger.info(
        f"Evaluation complete for {arch}! Accuracy: {results['test_accuracy_pct']}%, Macro F1: {results['macro_f1']}, Latency: {results['avg_latency_ms']}ms."
    )
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate a trained KrishiNetra model")
    parser.add_argument("--arch", type=str, default="efficientnet_b3", choices=["efficientnet_b3", "resnet50", "mobilenet_v2"])
    parser.add_argument("--data_dir", type=str, default="dataset/data")
    parser.add_argument("--weights", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default="models/reports")
    parser.add_argument("--batch_size", type=int, default=16)
    args = parser.parse_args()

    evaluate_model(
        arch=args.arch,
        data_dir=args.data_dir,
        weights_path=args.weights,
        output_dir=args.output_dir,
        batch_size=args.batch_size
    )
