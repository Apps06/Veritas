"""
Custom Model Training Script for Veritas
Fine-tunes a Vision Transformer on collected training data
"""
import os
import torch
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from transformers import (
    ViTForImageClassification,
    ViTImageProcessor,
    TrainingArguments,
    Trainer
)
from sklearn.model_selection import train_test_split
import numpy as np


class ImageDataset(Dataset):
    """Custom dataset for AI vs Real image classification"""
    
    def __init__(self, image_paths, labels, processor):
        self.image_paths = image_paths
        self.labels = labels
        self.processor = processor
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image = Image.open(self.image_paths[idx]).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.squeeze(0) for k, v in inputs.items()}
        inputs["labels"] = torch.tensor(self.labels[idx])
        return inputs


def load_dataset(data_dir="training_data"):
    """Load images from training_data directory"""
    data_path = Path(data_dir)
    ai_dir = data_path / "ai"
    real_dir = data_path / "real"
    
    image_paths = []
    labels = []
    
    # Label 0 = AI, Label 1 = Real
    if ai_dir.exists():
        for img_path in ai_dir.glob("*"):
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                image_paths.append(str(img_path))
                labels.append(0)  # AI
    
    if real_dir.exists():
        for img_path in real_dir.glob("*"):
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                image_paths.append(str(img_path))
                labels.append(1)  # Real
    
    print(f"Loaded {len(image_paths)} images ({labels.count(0)} AI, {labels.count(1)} Real)")
    return image_paths, labels


def compute_metrics(eval_pred):
    """Compute accuracy metrics"""
    predictions = np.argmax(eval_pred.predictions, axis=-1)
    accuracy = (predictions == eval_pred.label_ids).mean()
    return {"accuracy": accuracy}


def train_model(data_dir="training_data", output_dir="models/veritas_detector", epochs=5):
    """Train custom detector model"""
    print("=" * 50)
    print("Veritas Custom Model Training")
    print("=" * 50)
    
    # Load data
    image_paths, labels = load_dataset(data_dir)
    
    if len(image_paths) < 20:
        print("⚠️  Not enough training data! Please run image_scraper.py first.")
        return None
    
    # Split data
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        image_paths, labels, test_size=0.2, stratify=labels, random_state=42
    )
    
    print(f"Training set: {len(train_paths)} images")
    print(f"Validation set: {len(val_paths)} images")
    
    # Load pre-trained model and processor
    model_name = "google/vit-base-patch16-224"
    print(f"\nLoading base model: {model_name}")
    
    processor = ViTImageProcessor.from_pretrained(model_name)
    model = ViTForImageClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label={0: "AI_Generated", 1: "Real"},
        label2id={"AI_Generated": 0, "Real": 1},
        ignore_mismatched_sizes=True
    )
    
    # Create datasets
    train_dataset = ImageDataset(train_paths, train_labels, processor)
    val_dataset = ImageDataset(val_paths, val_labels, processor)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        push_to_hub=False,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )
    
    # Train
    print("\n🚀 Starting training...")
    trainer.train()
    
    # Save final model
    final_path = Path(output_dir) / "final"
    trainer.save_model(str(final_path))
    processor.save_pretrained(str(final_path))
    
    print(f"\n✓ Model saved to: {final_path.absolute()}")
    
    # Evaluate
    results = trainer.evaluate()
    print(f"\n📊 Final Accuracy: {results['eval_accuracy']*100:.2f}%")
    
    return str(final_path)


if __name__ == "__main__":
    train_model(epochs=5)
