"""
SoilChain AI Model Training
==============================
Trains a MobileNetV2-based soil classifier using transfer learning.
Output: models/soil_classifier.h5 (ready to plug into FastAPI backend)

Run: python train_model.py
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
)
from pathlib import Path
import matplotlib.pyplot as plt

# ── CONFIG ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data/processed")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_FROZEN = 10    # Phase 1: train only top layers
EPOCHS_FINETUNE = 10  # Phase 2: fine-tune last few base layers
LEARNING_RATE = 1e-3
FINETUNE_LR = 1e-5
CLASSES = ["degraded", "healthy", "moderate"]  # Alphabetical = TF default order
NUM_CLASSES = len(CLASSES)
# ─────────────────────────────────────────────────────────────────────────────


def check_gpu():
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"✅ GPU detected: {gpus[0].name}")
        # Allow memory growth to avoid OOM errors
        tf.config.experimental.set_memory_growth(gpus[0], True)
    else:
        print("⚠️  No GPU detected — training on CPU (will be slower)")


def build_data_loaders():
    """Create train, val, test data generators with augmentation on train."""
    print("\n📂 Loading dataset...")

    train_gen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=30,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        vertical_flip=True,
        brightness_range=[0.75, 1.25],
        shear_range=0.1,
        fill_mode="nearest"
    )

    val_test_gen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0 / 255
    )

    train_data = train_gen.flow_from_directory(
        DATA_DIR / "train",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True
    )

    val_data = val_test_gen.flow_from_directory(
        DATA_DIR / "val",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False
    )

    test_data = val_test_gen.flow_from_directory(
        DATA_DIR / "test",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False
    )

    print(f"  Train: {train_data.samples} images")
    print(f"  Val:   {val_data.samples} images")
    print(f"  Test:  {test_data.samples} images")
    print(f"  Classes: {train_data.class_indices}")

    # Save class indices for inference
    with open(MODEL_DIR / "class_indices.json", "w") as f:
        json.dump(train_data.class_indices, f)

    return train_data, val_data, test_data


def build_model():
    """Build MobileNetV2 transfer learning model."""
    print("\n🏗️  Building model...")

    base_model = MobileNetV2(
        weights="imagenet",
        include_top=False,
        input_shape=(*IMG_SIZE, 3)
    )
    base_model.trainable = False  # Freeze all base layers initially

    # Custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.4)(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.3)(x)
    output = Dense(NUM_CLASSES, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=output)

    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")]
    )

    print(f"  Total params: {model.count_params():,}")
    print(f"  Trainable params: {sum([tf.size(w).numpy() for w in model.trainable_weights]):,}")

    return model, base_model


def get_callbacks(phase: str):
    """Callbacks for training monitoring and early stopping."""
    return [
        ModelCheckpoint(
            filepath=str(MODEL_DIR / f"best_model_{phase}.h5"),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),
        TensorBoard(
            log_dir=f"logs/{phase}",
            histogram_freq=1
        )
    ]


def plot_training_history(history, phase: str):
    """Save accuracy and loss plots."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(history.history["accuracy"], label="Train Accuracy")
    axes[0].plot(history.history["val_accuracy"], label="Val Accuracy")
    axes[0].set_title(f"Model Accuracy — {phase}")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history.history["loss"], label="Train Loss")
    axes[1].plot(history.history["val_loss"], label="Val Loss")
    axes[1].set_title(f"Model Loss — {phase}")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(MODEL_DIR / f"training_plot_{phase}.png", dpi=150)
    plt.close()
    print(f"  📊 Plot saved: models/training_plot_{phase}.png")


def evaluate_model(model, test_data):
    """Evaluate on test set and print detailed metrics."""
    from sklearn.metrics import classification_report, confusion_matrix
    import seaborn as sns

    print("\n📊 Evaluating on test set...")
    test_loss, test_acc, test_auc = model.evaluate(test_data, verbose=0)
    print(f"  Test Accuracy: {test_acc:.4f} ({test_acc*100:.1f}%)")
    print(f"  Test AUC:      {test_auc:.4f}")
    print(f"  Test Loss:     {test_loss:.4f}")

    # Detailed classification report
    y_pred = np.argmax(model.predict(test_data, verbose=0), axis=1)
    y_true = test_data.classes

    print("\n📋 Classification Report:")
    print(classification_report(y_true, y_pred, target_names=CLASSES))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=CLASSES, yticklabels=CLASSES)
    plt.title("Confusion Matrix — SoilChain Classifier")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(MODEL_DIR / "confusion_matrix.png", dpi=150)
    plt.close()
    print("  📊 Confusion matrix saved: models/confusion_matrix.png")

    return test_acc


def train():
    print("=" * 55)
    print("  SoilChain AI Model Training")
    print("=" * 55)

    check_gpu()
    train_data, val_data, test_data = build_data_loaders()
    model, base_model = build_model()

    # ── PHASE 1: Train only the custom head (base frozen) ──────────────────
    print(f"\n🚀 Phase 1: Training classification head ({EPOCHS_FROZEN} epochs)...")
    history1 = model.fit(
        train_data,
        epochs=EPOCHS_FROZEN,
        validation_data=val_data,
        callbacks=get_callbacks("phase1"),
        verbose=1
    )
    plot_training_history(history1, "phase1")

    # ── PHASE 2: Fine-tune last 30 layers of base model ───────────────────
    print(f"\n🔧 Phase 2: Fine-tuning last 30 base layers ({EPOCHS_FINETUNE} epochs)...")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=Adam(learning_rate=FINETUNE_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")]
    )

    history2 = model.fit(
        train_data,
        epochs=EPOCHS_FINETUNE,
        validation_data=val_data,
        callbacks=get_callbacks("phase2"),
        verbose=1
    )
    plot_training_history(history2, "phase2")

    # ── EVALUATE ───────────────────────────────────────────────────────────
    test_acc = evaluate_model(model, test_data)

    # ── SAVE FINAL MODEL ───────────────────────────────────────────────────
    final_path = MODEL_DIR / "soil_classifier.h5"
    model.save(str(final_path))
    print(f"\n✅ Final model saved: {final_path}")
    print(f"   Test Accuracy: {test_acc*100:.1f}%")

    if test_acc >= 0.85:
        print("   🎉 Excellent! Ready to plug into the FastAPI backend.")
    elif test_acc >= 0.75:
        print("   ⚠️  Decent. Consider collecting more images per class.")
    else:
        print("   ❌ Low accuracy. Run augment_data.py and retrain.")

    print("\n📋 Next step: python scripts/test_inference.py")


if __name__ == "__main__":
    train()
