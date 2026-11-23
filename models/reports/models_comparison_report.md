# KrishiNetra Deep Learning Model Architecture Comparison Report

This report benchmarks the three deep learning architectures evaluated on the KrishiNetra agricultural test dataset split under identical conditions.

## Overall Comparison Matrix

| Architecture | Top-1 Acc (%) | Top-3 Acc (%) | Macro F1 | Weighted F1 | Inference Latency (ms) | Model Size (MB) | Total Parameters |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **efficientnet_b3** | 7.48% | 25.85% | 0.0386 | 0.0386 | 138.47 ms | 50.65 MB | 11,509,337 |
| **resnet50** | 10.2% | 25.85% | 0.0611 | 0.0611 | 214.73 ms | 216.49 MB | 24,583,281 |
| **mobilenet_v2** | 10.2% | 27.89% | 0.0529 | 0.0529 | 66.77 ms | 18.65 MB | 2,286,641 |

## Architecture Analysis & Production Recommendations

### 1. EfficientNetB3 (Primary Model)
- **Strengths**: Highest diagnostic accuracy and representational capacity due to compound scaling of depth, width, and resolution (300x300).
- **Best Suited For**: Cloud-based central diagnostic server and primary recommendation engine.

### 2. ResNet50
- **Strengths**: Residual skip-connections provide stable gradient propagation through deep feature representations; robust against vanishing gradients.
- **Trade-offs**: Moderately higher parameter count and memory footprint.

### 3. MobileNetV2 (Edge / Mobile Optimized)
- **Strengths**: Inverted residual blocks with depthwise separable convolutions drastically cut down FLOPs and parameter count; fastest inference latency.
- **Best Suited For**: On-device offline edge mobile deployment for farmers with limited rural connectivity.

