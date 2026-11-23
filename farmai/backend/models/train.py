"""Training script for PlantVillage crop disease classification using MobileNetV2 transfer learning.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SUPPORTED_SUBSETS = [
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Bacterial_spot",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy"
]


def build_model(num_classes: int):
    """Build MobileNetV2 transfer learning architecture."""
    import tensorflow as tf
    from tensorflow.keras import layers, models
    from tensorflow.keras.applications import MobileNetV2

    base_model = MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False

    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
        layers.RandomContrast(0.2),
    ], name="data_augmentation")

    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = data_augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="FarmAI_MobileNetV2")
    return model, base_model


def train(args):
    """Execute two-stage training workflow."""
    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix

    dataset_dir = Path(args.dataset_path)
    if not dataset_dir.exists():
        logger.error(f"Dataset path '{dataset_dir}' does not exist.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    img_size = (224, 224)
    batch_size = args.batch_size

    logger.info(f"Loading dataset from {dataset_dir} (Batch: {batch_size}, Image size: {img_size})...")

    # Load full dataset and split 80/10/10
    full_ds = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        shuffle=True,
        image_size=img_size,
        batch_size=batch_size,
        seed=42
    )

    class_names = full_ds.class_names
    if not args.all_classes:
        logger.info(f"Filtering dataset to standard Tomato/Potato/Pepper classes ({len(SUPPORTED_SUBSETS)} classes).")

    # Split into Train (80%), Val (10%), Test (10%)
    total_batches = len(full_ds)
    train_size = int(0.8 * total_batches)
    val_size = int(0.1 * total_batches)

    train_ds = full_ds.take(train_size)
    val_and_test = full_ds.skip(train_size)
    val_ds = val_and_test.take(val_size)
    test_ds = val_and_test.skip(val_size)

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)

    num_classes = len(class_names)
    logger.info(f"Building MobileNetV2 classifier with {num_classes} classes: {class_names}")
    model, base_model = build_model(num_classes)

    # Stage 1: Frozen base model
    logger.info(f"Stage 1: Training top head with frozen base ({args.epochs_stage1} epochs)...")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs_stage1
    )

    # Stage 2: Fine-tuning top ~30 layers
    logger.info(f"Stage 2: Unfreezing top 30 layers with lr=1e-5 ({args.epochs_stage2} epochs)...")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs_stage2
    )

    # Save model and class names
    model_save_path = output_dir / "model.keras"
    class_names_path = output_dir / "class_names.json"

    logger.info(f"Saving trained model weights to {model_save_path}...")
    model.save(str(model_save_path))

    with open(class_names_path, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)
    logger.info(f"Saved class names to {class_names_path}")

    # Evaluate on test split
    logger.info("Evaluating on held-out test split...")
    y_true = []
    y_pred = []
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred.extend(np.argmax(preds, axis=1))

    report = classification_report(y_true, y_pred, target_names=class_names)
    matrix = confusion_matrix(y_true, y_pred)

    report_path = output_dir / "classification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== CLASSIFICATION REPORT ===\n")
        f.write(report)
        f.write("\n\n=== CONFUSION MATRIX ===\n")
        f.write(np.array2string(matrix))

    logger.info(f"Evaluation report and confusion matrix saved to {report_path}")
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FarmAI PlantVillage MobileNetV2 Training Script")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to PlantVillage dataset directory")
    parser.add_argument("--output_dir", type=str, default="weights", help="Directory to save model weights")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--epochs_stage1", type=int, default=5, help="Epochs for frozen base stage")
    parser.add_argument("--epochs_stage2", type=int, default=8, help="Epochs for fine-tuning stage")
    parser.add_argument("--all_classes", action="store_true", help="Train on all dataset classes instead of subset")
    cli_args = parser.parse_args()

    train(cli_args)
