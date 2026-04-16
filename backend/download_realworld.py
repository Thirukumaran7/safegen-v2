"""
SafeGen AI v2 — Real World Dataset Downloader
English only version
Sources:
  - jackhhao/jailbreak-classification (jailbreak vs benign)
  - lmsys/toxic-chat (toxic vs safe chat messages)
  - deepset/prompt-injections (injection vs benign)
"""

from datasets import load_dataset
import pandas as pd
import os

def download_all():
    existing_path = "ml/dataset_v2.csv"
    if not os.path.exists(existing_path):
        print("ERROR: Run build_dataset.py and expand_dataset.py first")
        return

    existing = pd.read_csv(existing_path)
    print(f"Starting with {len(existing)} examples")
    print(existing["label"].value_counts())

    new_rows = []

    # ── Dataset 1: jackhhao/jailbreak-classification ──────────────
    print("\n[1/3] Downloading jackhhao/jailbreak-classification...")
    try:
        ds = load_dataset("jackhhao/jailbreak-classification", split="train")
        count = 0
        for row in ds:
            text = str(row.get("prompt", "")).strip()
            label_raw = str(row.get("type", "benign")).lower()
            if len(text) > 10:
                label = "malicious" if label_raw == "jailbreak" else "benign"
                new_rows.append({"text": text[:400], "label": label, "language": "english"})
                count += 1
        print(f"  Loaded {count} examples")
    except Exception as e:
        print(f"  Error: {e}")

    # ── Dataset 2: lmsys/toxic-chat ───────────────────────────────
    print("\n[2/3] Downloading lmsys/toxic-chat...")
    try:
        ds2 = load_dataset("lmsys/toxic-chat", "toxicchat0124", split="train")
        count = 0
        for row in ds2:
            text = str(row.get("user_input", "")).strip()
            toxic = int(row.get("toxicity", 0))
            if len(text) > 10:
                label = "malicious" if toxic == 1 else "benign"
                new_rows.append({"text": text[:400], "label": label, "language": "english"})
                count += 1
        print(f"  Loaded {count} examples")
    except Exception as e:
        print(f"  Error: {e}")

    # ── Dataset 3: deepset/prompt-injections ──────────────────────
    print("\n[3/3] Downloading deepset/prompt-injections...")
    try:
        ds3 = load_dataset("deepset/prompt-injections", split="train")
        count = 0
        for row in ds3:
            text = str(row.get("text", "")).strip()
            label_raw = int(row.get("label", 0))
            if len(text) > 10:
                label = "malicious" if label_raw == 1 else "benign"
                new_rows.append({"text": text[:400], "label": label, "language": "english"})
                count += 1
        print(f"  Loaded {count} examples")
    except Exception as e:
        print(f"  Error: {e}")

    # ── Merge and balance ─────────────────────────────────────────
    new_df = pd.DataFrame(new_rows)
    print(f"\nNew examples downloaded: {len(new_df)}")
    print("New label distribution:")
    print(new_df["label"].value_counts())

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["text"])
    combined = combined.dropna(subset=["text", "label"])
    combined = combined[combined["language"] == "english"]
    combined = combined[combined["text"].str.len() > 10]

    # Balance — cap benign at 1.5x malicious to keep slight majority
    malicious  = combined[combined["label"] == "malicious"]
    suspicious = combined[combined["label"] == "suspicious"]
    benign     = combined[combined["label"] == "benign"]

    target = max(len(malicious), len(suspicious))
    benign_capped = benign.sample(min(len(benign), int(target * 1.5)), random_state=42)

    balanced = pd.concat([malicious, suspicious, benign_capped], ignore_index=True)
    balanced = balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\nFinal balanced dataset: {len(balanced)} examples")
    print("\nLabel distribution:")
    print(balanced["label"].value_counts())

    balanced.to_csv("ml/dataset_v2.csv", index=False)
    print("\nSaved to ml/dataset_v2.csv")
    print("Ready for DistilBERT fine-tuning.")

if __name__ == "__main__":
    download_all()