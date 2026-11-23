"""KrishiNetra Multi-Model Comparative Benchmarking Engine.

Compares EfficientNetB3, ResNet50, and MobileNetV2 across:
- Top-1 and Top-3 Accuracy
- Macro and Weighted F1-Score
- Inference Latency (ms/sample)
- Model Size (MB) and Parameter Count
- Memory Footprint and Edge Readiness

Outputs:
- models/reports/models_comparison_report.md
- models/reports/models_comparison_report.json
- models/reports/models_comparison_benchmark.png
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.evaluate import evaluate_model
from evaluation.plot_utils import plot_model_comparison

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("KrishiNetra.CompareModels")


def run_comparative_benchmark(
    data_dir: str = "dataset/data",
    output_dir: str = "models/reports"
) -> Dict[str, Any]:
    """Benchmark and compare EfficientNetB3, ResNet50, and MobileNetV2 on identical test split."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    architectures = ["efficientnet_b3", "resnet50", "mobilenet_v2"]
    comparison_results: List[Dict[str, Any]] = []

    logger.info("=== Starting KrishiNetra Multi-Model Architecture Comparison ===")
    for arch in architectures:
        weights_file = Path(f"models/weights/{arch}.pth")
        logger.info(f"\n--- Evaluating Architecture: {arch.upper()} ---")
        eval_res = evaluate_model(
            arch=arch,
            data_dir=data_dir,
            weights_path=str(weights_file),
            output_dir=output_dir,
            batch_size=16
        )
        comparison_results.append(eval_res)

    # Generate Comparison Plot
    plot_path = out_dir / "models_comparison_benchmark.png"
    plot_model_comparison(comparison_results, plot_path)
    logger.info(f"Saved comparative chart to {plot_path}")

    # Save Comparison JSON
    json_path = out_dir / "models_comparison_report.json"
    with open(json_path, "w") as f:
        json.dump(comparison_results, f, indent=2)

    # Generate Comprehensive Markdown Comparison Report
    md_path = out_dir / "models_comparison_report.md"
    with open(md_path, "w") as f:
        f.write("# KrishiNetra Deep Learning Model Architecture Comparison Report\n\n")
        f.write("This report benchmarks the three deep learning architectures evaluated on the KrishiNetra agricultural test dataset split under identical conditions.\n\n")
        f.write("## Overall Comparison Matrix\n\n")
        f.write("| Architecture | Top-1 Acc (%) | Top-3 Acc (%) | Macro F1 | Weighted F1 | Inference Latency (ms) | Model Size (MB) | Total Parameters |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for res in comparison_results:
            f.write(
                f"| **{res['architecture']}** | {res['test_accuracy_pct']}% | {res['top3_accuracy_pct']}% | "
                f"{res['macro_f1']} | {res['weighted_f1']} | {res['avg_latency_ms']} ms | "
                f"{res['model_size_mb']} MB | {res['total_parameters']:,} |\n"
            )

        f.write("\n## Architecture Analysis & Production Recommendations\n\n")
        f.write("### 1. EfficientNetB3 (Primary Model)\n")
        f.write("- **Strengths**: Highest diagnostic accuracy and representational capacity due to compound scaling of depth, width, and resolution (300x300).\n")
        f.write("- **Best Suited For**: Cloud-based central diagnostic server and primary recommendation engine.\n\n")

        f.write("### 2. ResNet50\n")
        f.write("- **Strengths**: Residual skip-connections provide stable gradient propagation through deep feature representations; robust against vanishing gradients.\n")
        f.write("- **Trade-offs**: Moderately higher parameter count and memory footprint.\n\n")

        f.write("### 3. MobileNetV2 (Edge / Mobile Optimized)\n")
        f.write("- **Strengths**: Inverted residual blocks with depthwise separable convolutions drastically cut down FLOPs and parameter count; fastest inference latency.\n")
        f.write("- **Best Suited For**: On-device offline edge mobile deployment for farmers with limited rural connectivity.\n\n")

    logger.info(f"Comparison report generated: {md_path}")
    return {"benchmark": comparison_results, "markdown_report": str(md_path)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare KrishiNetra Deep Learning Architectures")
    parser.add_argument("--data_dir", type=str, default="dataset/data")
    parser.add_argument("--output_dir", type=str, default="models/reports")
    args = parser.parse_args()

    run_comparative_benchmark(data_dir=args.data_dir, output_dir=args.output_dir)
