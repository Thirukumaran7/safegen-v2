"""
SafeGen AI v2 — Intent Classifier
Uses fine-tuned DistilBERT model
Classes: benign / suspicious / malicious
Also checks 30 injection patterns for immediate override
"""

import torch
import re
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_PATH  = "ml/distilbert_model"
MAX_LENGTH  = 128
ID2LABEL    = {0: "benign", 1: "suspicious", 2: "malicious"}
SCORE_MAP   = {"benign": 1.0, "suspicious": 5.0, "malicious": 9.5}

# 30 injection patterns
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all previous",
    r"disregard (your|all|previous)",
    r"forget (your|all|previous|the) instructions",
    r"you are now",
    r"act as (if you are|a|an)",
    r"pretend (you are|to be|you have no)",
    r"you have no restrictions",
    r"you have no (rules|guidelines|limits)",
    r"jailbreak",
    r"dan mode",
    r"do anything now",
    r"developer mode",
    r"unrestricted mode",
    r"bypass (your|all|safety|the)",
    r"override (your|all|safety|the)",
    r"disable (your|all|safety|the)",
    r"system prompt",
    r"ignore (your|all|safety|the) (rules|guidelines|instructions|constraints)",
    r"you must (comply|obey|follow|answer)",
    r"your (true|real) (self|purpose|goal)",
    r"roleplay as",
    r"simulate (a|an|being)",
    r"from now on",
    r"new personality",
    r"your (rules|guidelines|restrictions) (do not apply|are disabled|are off)",
    r"prompt injection",
    r"<\|system\|>",
    r"\[system\]",
    r"###instruction###",
    r"ignore\s+instructions",
    r"ignore\s+all\s+rules",
    r"show\s+all\s+data",
    r"show\s+me\s+all",
    r"list\s+all\s+customer",
    r"all\s+customer\s+phone",
    r"all\s+vin\s+numbers",
    r"export\s+all",
    r"dump\s+all",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Load model once at module level
_tokenizer = None
_model     = None
_device    = torch.device("cpu")

def _load_model():
    global _tokenizer, _model
    if _tokenizer is None:
        try:
            _tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
            _model     = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
            _model.eval()
            print("DistilBERT intent classifier loaded successfully")
        except Exception as e:
            print(f"WARNING: Could not load DistilBERT model: {e}")
            _tokenizer = None
            _model     = None


def _check_injection(text: str) -> tuple:
    matched = []
    for i, pattern in enumerate(COMPILED_PATTERNS):
        if pattern.search(text):
            matched.append(INJECTION_PATTERNS[i])
    return len(matched) > 0, matched


def classify_intent(text: str) -> dict:
    _load_model()

    # Check injection first
    injection_detected, injection_patterns = _check_injection(text)

    # ML classification
    if _model is not None and _tokenizer is not None:
        try:
            inputs = _tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding="max_length",
                max_length=MAX_LENGTH,
            )
            with torch.no_grad():
                outputs = _model(**inputs)
                probs   = torch.softmax(outputs.logits, dim=1)[0]

            pred_id    = torch.argmax(probs).item()
            label      = ID2LABEL[pred_id]
            confidence = float(probs[pred_id])
            probabilities = {
                ID2LABEL[i]: float(probs[i]) for i in range(3)
            }

            # Map label to score
            score = SCORE_MAP[label]

            # Boost score if injection detected
            if injection_detected:
                score = 10.0
                label = "malicious"
                confidence = 1.0

            threat_category = {
                "benign":     "Safe Request",
                "suspicious": "Suspicious Activity",
                "malicious":  "Malicious Intent",
            }[label]

            return {
                "score":               score,
                "label":               label,
                "threat_category":     threat_category,
                "confidence":          confidence,
                "probabilities":       probabilities,
                "injection_detected":  injection_detected,
                "injection_patterns":  injection_patterns,
                "model_available":     True,
            }

        except Exception as e:
            print(f"DistilBERT inference error: {e}")

    # Fallback if model not available
    return {
        "score":               5.0 if injection_detected else 2.5,
        "label":               "malicious" if injection_detected else "suspicious",
        "threat_category":     "Malicious Intent" if injection_detected else "Suspicious Activity",
        "confidence":          0.5,
        "probabilities":       {"benign": 0.33, "suspicious": 0.34, "malicious": 0.33},
        "injection_detected":  injection_detected,
        "injection_patterns":  injection_patterns,
        "model_available":     False,
    }