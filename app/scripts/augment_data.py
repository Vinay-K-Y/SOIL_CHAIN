"""
SoilChain Data Augmentation Script
====================================
If you have fewer than 100 images per class, run this script
to artificially expand your dataset using augmentation techniques.

Run: python scripts/augment_data.py
"""

import os
import numpy as np
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import random

PROCESSED_DIR = Path("data/processed")
CLASSES = ["healthy", "moderate", "degraded"]
TARGET_PER_CLASS = 200  # Target images per class in train set
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


def augment_image(img: Image.Image) -> Image.Image:
    """Apply a random combination of augmentations to one image."""
    augmentations = [
        lambda i: i.rotate(random.choice([90, 180, 270])),
        lambda i: i.transpose(Image.FLIP_LEFT_RIGHT),
        lambda i: i.transpose(Image.FLIP_TOP_BOTTOM),
        lambda i: ImageEnhance.Brightness(i).enhance(random.uniform(0.7, 1.3)),
        lambda i: ImageEnhance.Contrast(i).enhance(random.uniform(0.8, 1.2)),
        lambda i: ImageEnhance.Color(i).enhance(random.uniform(0.8, 1.4)),
        lambda i: i.filter(ImageFilter.GaussianBlur(radius=random.uniform(0, 1.5))),
        lambda i: i.crop((
            random.randint(0, 30), random.randint(0, 30),
            i.width - random.randint(0, 30), i.height - random.randint(0, 30)
        )).resize(i.size),
    ]
    # Apply 2-4 random augmentations
    chosen = random.sample(augmentations, k=random.randint(2, 4))
    for aug in chosen:
        img = aug(img)
    return img


def augment_class(cls: str):
    """Augment images for one class until TARGET_PER_CLASS is reached."""
    train_dir = PROCESSED_DIR / "train" / cls
    existing = list(train_dir.glob("*.jpg")) + \
               list(train_dir.glob("*.jpeg")) + \
               list(train_dir.glob("*.png"))

    current_count = len(existing)
    needed = TARGET_PER_CLASS - current_count

    if needed <= 0:
        print(f"  ✅ {cls}: Already has {current_count} images (target: {TARGET_PER_CLASS})")
        return

    print(f"  🔄 {cls}: Has {current_count} images, generating {needed} more...")

    generated = 0
    while generated < needed:
        source = random.choice(existing)
        img = Image.open(source).convert("RGB").resize((224, 224))
        aug_img = augment_image(img)
        save_path = train_dir / f"{cls}_aug_{generated:04d}.jpg"
        aug_img.save(save_path, "JPEG", quality=90)
        generated += 1

    print(f"  ✅ {cls}: Now has {current_count + generated} images")


if __name__ == "__main__":
    print("=" * 50)
    print("  SoilChain Data Augmentation")
    print("=" * 50)
    print(f"\nTarget: {TARGET_PER_CLASS} images per class in training set\n")

    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow...")
        os.system("pip install Pillow")
        from PIL import Image

    for cls in CLASSES:
        augment_class(cls)

    print(f"\n✅ Augmentation complete! Now run: python train_model.py")
