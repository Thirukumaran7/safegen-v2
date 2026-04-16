"""
SafeGen AI v2 — DistilBERT Fine-tuning Script
Model: distilbert-base-uncased
Task: 3-class intent classification (benign / suspicious / malicious)
Dataset: ml/dataset_v2.csv (4068 examples, balanced)
"""

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)
from torch.optim import AdamW
import time

# ── Config ────────────────────────────────────────────────────────
MODEL_NAME   = "distilbert-base-uncased"
DATASET_PATH = "ml/dataset_v2.csv"
OUTPUT_DIR   = "ml/distilbert_model"
MAX_LENGTH   = 128
BATCH_SIZE   = 16
EPOCHS       = 4
LEARNING_RATE = 2e-5
WARMUP_RATIO  = 0.1
SEED          = 42

LABEL2ID = {"benign": 0, "suspicious": 1, "malicious": 2}
ID2LABEL = {0: "benign", 1: "suspicious", 2: "malicious"}

torch.manual_seed(SEED)
np.random.seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# ── Dataset class ─────────────────────────────────────────────────
class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt",
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "input_ids":      self.encodings["input_ids"][idx],
            "attention_mask": self.encodings["attention_mask"][idx],
            "labels":         self.labels[idx],
        }

# ── Load data ─────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna(subset=["text", "label"])
    df = df[df["label"].isin(LABEL2ID.keys())]
    df["text"]  = df["text"].astype(str).str.strip()
    df["label_id"] = df["label"].map(LABEL2ID)

    print(f"\nDataset loaded: {len(df)} examples")
    print("Label distribution:")
    print(df["label"].value_counts())

    texts  = df["text"].tolist()
    labels = df["label_id"].tolist()

    return train_test_split(
        texts, labels,
        test_size=0.2,
        random_state=SEED,
        stratify=labels,
    )

# ── Evaluate ──────────────────────────────────────────────────────
def evaluate(model, loader):
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch in loader:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels         = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds   = torch.argmax(outputs.logits, dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    return all_labels, all_preds

# ── Main training ─────────────────────────────────────────────────
def train():
    print("=" * 60)
    print("SafeGen AI v2 — DistilBERT Fine-tuning")
    print("=" * 60)

    # Load data
    train_texts, test_texts, train_labels, test_labels = load_data()
    print(f"\nTrain: {len(train_texts)} | Test: {len(test_texts)}")

    # Load tokenizer
    print(f"\nLoading tokenizer: {MODEL_NAME}")
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

    # Tokenize
    print("Tokenizing...")
    train_dataset = IntentDataset(train_texts, train_labels, tokenizer, MAX_LENGTH)
    test_dataset  = IntentDataset(test_texts,  test_labels,  tokenizer, MAX_LENGTH)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader  = DataLoader(test_dataset,  batch_size=BATCH_SIZE, shuffle=False)

    # Load model
    print(f"Loading model: {MODEL_NAME}")
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=3,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(device)

    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    total_steps   = len(train_loader) * EPOCHS
    warmup_steps  = int(total_steps * WARMUP_RATIO)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    print(f"\nTraining config:")
    print(f"  Epochs:        {EPOCHS}")
    print(f"  Batch size:    {BATCH_SIZE}")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Total steps:   {total_steps}")
    print(f"  Warmup steps:  {warmup_steps}")
    print("=" * 60)

    best_accuracy = 0.0

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        start_time = time.time()

        for step, batch in enumerate(train_loader):
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels         = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

            if (step + 1) % 20 == 0:
                elapsed = time.time() - start_time
                avg_loss = total_loss / (step + 1)
                print(f"  Epoch {epoch+1} | Step {step+1}/{len(train_loader)} | Loss: {avg_loss:.4f} | Time: {elapsed:.1f}s")

        # Evaluate after each epoch
        avg_train_loss = total_loss / len(train_loader)
        all_labels, all_preds = evaluate(model, test_loader)
        accuracy = accuracy_score(all_labels, all_preds)

        print(f"\nEpoch {epoch+1}/{EPOCHS} complete")
        print(f"  Train Loss: {avg_train_loss:.4f}")
        print(f"  Test Accuracy: {accuracy:.4f}")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            model.save_pretrained(OUTPUT_DIR)
            tokenizer.save_pretrained(OUTPUT_DIR)
            print(f"  ✓ Best model saved to {OUTPUT_DIR}")

        print()

    # Final evaluation
    print("=" * 60)
    print("FINAL EVALUATION (best model)")
    print("=" * 60)

    best_model = DistilBertForSequenceClassification.from_pretrained(OUTPUT_DIR)
    best_model.to(device)
    all_labels, all_preds = evaluate(best_model, test_loader)

    print("\nCLASSIFICATION REPORT")
    print(classification_report(
        all_labels, all_preds,
        target_names=["benign", "suspicious", "malicious"]
    ))

    print("CONFUSION MATRIX")
    print(confusion_matrix(all_labels, all_preds))
    print(f"\nBest Accuracy: {best_accuracy:.4f}")
    print(f"Model saved to: {OUTPUT_DIR}")
    print("\nTraining complete.")

if __name__ == "__main__":
    train()