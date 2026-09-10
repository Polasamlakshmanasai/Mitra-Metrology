# app/services/ocr_service.py
"""
OCR Service bridging FastAPI backend with the AI computer vision engine.
"""

import os
import sys
from pathlib import Path

# Ensure ai_engine directory is in sys.path
for root in [
    Path(__file__).resolve().parent.parent.parent.parent,
    Path(__file__).resolve().parent.parent.parent,
    Path("/app")
]:
    ai_dir = root / "ai_engine"
    if ai_dir.is_dir():
        if str(ai_dir) not in sys.path:
            sys.path.insert(0, str(ai_dir))
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

import cv2
from image_quality import assess_image_quality
from preprocessing import preprocess_image
from ocr import run_ocr, group_ocr_lines, combine_ocr_text
from barcode import detect_barcodes


def analyze_image_ocr(image_path: str):
    """
    Executes image quality check, preprocessing, OCR text detection, and barcode scanning.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    # 1. Image Quality Assessment
    quality = assess_image_quality(image)

    # 2. Image Preprocessing
    preprocessed = preprocess_image(image)
    ocr_image = preprocessed["enhanced"]

    # 3. OCR Run
    ocr_words = run_ocr(ocr_image)
    ocr_lines = group_ocr_lines(ocr_words)
    combined_text = combine_ocr_text(ocr_words)

    # 4. Barcode detection
    barcodes = detect_barcodes(image)

    return {
        "image_path": image_path,
        "quality": quality,
        "ocr_words": ocr_words,
        "ocr_lines": ocr_lines,
        "combined_text": combined_text,
        "barcodes": barcodes
    }
