"""
SoilChain Dataset Preparation Script
=====================================
Downloads soil image datasets from Kaggle and organizes them into
3 classes: healthy, moderate, degraded

BEFORE RUNNING:
1. pip install kaggle
2. Go to kaggle.com → Account → API → Create New Token
3. Download kaggle.json and place it at:
   - Windows: C:/Users/YourName/.kaggle/kaggle.json
   - Linux/Mac: ~/.kaggle/kaggle.json
4. Run: python scripts/prepare_dataset.py
"""

import os
import shutil
import random
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CLASSES = ["healthy", "moderate", "degraded"]
SPLITS = ["train", "val", "test"]
SPLIT_RATIOS = (0.70, 0.15, 0.15)  # train / val / test
SEED = 42
# ─────────────────────────────────────────────────────────────────────────────


def download_datasets():
    """Download soil datasets from Kaggle."""
    print("\n📥 Downloading datasets from Kaggle...")
    os.makedirs(RAW_DIR, exist_ok=True)

    datasets = [
        # Soil classification dataset with healthy/degraded labels
        ("prasanshasatpathy/soil-types", "soil-types"),
        # Additional soil images for more diversity
        ("jayaprakashpondy/soil-image-dataset", "soil-image-dataset"),
    ]

    for dataset_id, folder_name in datasets:
        dest = RAW_DIR / folder_name
        if dest.exists():
            print(f"  ✅ Already downloaded: {folder_name}")
            continue
        print(f"  ⬇️  Downloading: {dataset_id}")
        os.system(f"kaggle datasets download -d {dataset_id} -p {RAW_DIR} --unzip")
        print(f"  ✅ Done: {folder_name}")

    print("\n✅ All datasets downloaded!")


def create_folder_structure():
    """Create train/val/test folders for each class."""
    print("\n📁 Creating folder structure...")
    for split in SPLITS:
        for cls in CLASSES:
            path = PROCESSED_DIR / split / cls
            path.mkdir(parents=True, exist_ok=True)
    print("  ✅ Folders ready")


def map_raw_labels_to_classes(raw_label: str) -> str:
    """
    Maps raw dataset labels to our 3 SoilChain classes.
    Adjust this mapping based on whatever dataset you downloaded.
    """
    label = raw_label.lower().strip()

    healthy_keywords = ["healthy", "alluvial", "black", "loamy", "fertile", "good"]
    degraded_keywords = ["degraded", "sandy", "eroded", "arid", "poor", "clay"]

    if any(k in label for k in healthy_keywords):
        return "healthy"
    elif any(k in label for k in degraded_keywords):
        return "degraded"
    else:
        return "moderate"


def organize_images():
    """
    Scan raw downloaded folders, map labels, split into train/val/test.
    Works with any folder structure where subfolder name = label.
    """
    print("\n🔄 Organizing images into classes...")

    # Collect all images grouped by mapped class
    class_images = {cls: [] for cls in CLASSES}

    for raw_folder in RAW_DIR.rglob("*"):
        if not raw_folder.is_dir():
            continue
        mapped_class = map_raw_labels_to_classes(raw_folder.name)
        images = list(raw_folder.glob("*.jpg")) + \
                 list(raw_folder.glob("*.jpeg")) + \
                 list(raw_folder.glob("*.png"))
        if images:
            class_images[mapped_class].extend(images)
            print(f"  📂 {raw_folder.name} → [{mapped_class}] ({len(images)} images)")

    # Shuffle and split
    random.seed(SEED)
    total_copied = 0

    for cls, images in class_images.items():
        random.shuffle(images)
        n = len(images)
        if n == 0:
            print(f"  ⚠️  No images found for class: {cls}")
            continue

        n_train = int(n * SPLIT_RATIOS[0])
        n_val = int(n * SPLIT_RATIOS[1])

        splits_data = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:]
        }

        for split, split_images in splits_data.items():
            dest_dir = PROCESSED_DIR / split / cls
            for i, img_path in enumerate(split_images):
                dest = dest_dir / f"{cls}_{split}_{i:04d}{img_path.suffix}"
                shutil.copy2(img_path, dest)
            total_copied += len(split_images)
            print(f"  ✅ {cls}/{split}: {len(split_images)} images")

    print(f"\n✅ Total images organized: {total_copied}")


def verify_dataset():
    """Print a summary of the final dataset."""
    print("\n📊 Dataset Summary:")
    print(f"{'Class':<12} {'Train':<8} {'Val':<8} {'Test':<8} {'Total':<8}")
    print("-" * 44)

    for cls in CLASSES:
        counts = {}
        for split in SPLITS:
            folder = PROCESSED_DIR / split / cls
            counts[split] = len(list(folder.glob("*"))) if folder.exists() else 0
        total = sum(counts.values())
        print(f"{cls:<12} {counts['train']:<8} {counts['val']:<8} {counts['test']:<8} {total:<8}")

    print("\n💡 Tip: Aim for at least 100 images per class for good results.")
    print("   If you have fewer, run: python scripts/augment_data.py")


if __name__ == "__main__":
    print("=" * 50)
    print("  SoilChain Dataset Preparation")
    print("=" * 50)
    download_datasets()
    create_folder_structure()
    organize_images()
    verify_dataset()
    print("\n🚀 Dataset ready! Now run: python train_model.py")
